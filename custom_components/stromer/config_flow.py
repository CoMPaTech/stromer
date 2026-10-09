"""Config flow for Stromer integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiodns
import aiohttp
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import probatio

from .const import BIKE_DETAILS, CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, LOGGER
from .coordinator import StromerConfigEntry
from .stromer import ApiError, AuthenticationError, NextLocationError, Stromer

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_USERNAME): str,
        probatio.Required(probatio.Secret(CONF_PASSWORD)): str,
        probatio.Required(CONF_CLIENT_ID): str,
        probatio.Optional(probatio.Secret(CONF_CLIENT_SECRET)): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict:
    """Validate the user input allows us to connect by returning a dictionary with all bikes under the account."""
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    client_id = data[CONF_CLIENT_ID]
    client_secret = data.get(CONF_CLIENT_SECRET)

    # Initialize connection to stromer to validate credentials
    websession = async_create_clientsession(hass, auto_cleanup=False)
    stromer = Stromer(username, password, client_id, client_secret, websession)
    try:
        await stromer.stromer_connect()
        LOGGER.debug("Credentials validated successfully")

        # All bikes information available
        return await stromer.stromer_detect()
    except AuthenticationError as ex:
        raise InvalidAuth from ex
    except ApiError as ex:
        raise CannotConnect("Error while connecting to Stromer API %s", ex) from ex
    except NextLocationError as ex:
        raise CannotConnect("Error while getting authentication location %s", ex) from ex
    except (aiodns.error.DNSError, aiohttp.ClientError, TimeoutError) as ex:
        raise CannotConnect("Error while connecting to Stromer API %s", ex) from ex
    finally:
        websession.detach()


class StromerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stromer."""

    VERSION = 1

    async def async_step_bike(
        self, user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle selecting bike step."""
        if user_input is None:
            STEP_BIKE_DATA_SCHEMA = probatio.Schema(
                { probatio.Required(BIKE_DETAILS): probatio.In(list(self.friendly_names)), }
            )
            return self.async_show_form(
                step_id="bike", data_schema=STEP_BIKE_DATA_SCHEMA
            )

        # Rework user friendly name to actual bike id and details
        selected_bike = user_input[BIKE_DETAILS]
        bike_id = self.friendly_names[selected_bike]
        nickname = self.all_bikes[bike_id]["nickname"]
        self.user_input_data["bike_id"] = bike_id
        self.user_input_data["nickname"] = nickname
        self.user_input_data["model"] = self.all_bikes[bike_id]["biketype"]

        LOGGER.info(f"Using {selected_bike} (i.e. bike ID {bike_id}) to talk to the Stromer API")

        await self.async_set_unique_id(f"stromerbike-{bike_id}")
        self._abort_if_unique_id_configured()

        LOGGER.info(f"Creating entry using {nickname} as bike device name")
        return self.async_create_entry(title=nickname, data=self.user_input_data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            bikes_data = await validate_input(self.hass, user_input)
            LOGGER.debug(f"bikes_data contains {bikes_data}")

            # Retrieve any bikes available within account
            # Modify output for better display of selection
            self.friendly_names = {}
            self.all_bikes = {}
            LOGGER.debug("Checking available bikes:")
            for bike in bikes_data:
               LOGGER.debug(f"* this bike contains {bike}")
               bike_id = bike["bikeid"]
               nickname = bike["nickname"]
               biketype = bike["biketype"]

               friendly_name = f"{nickname} ({biketype}) #{bike_id}"

               self.friendly_names[friendly_name] = bike_id
               self.all_bikes[bike_id]= { "nickname": nickname, "biketype": biketype}

            # Save account info
            self.user_input_data = user_input
            return await self.async_step_bike()

        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _async_validate_existing_bike(self, entry: StromerConfigEntry, data: dict[str, Any]) -> dict[str, str]:
        """Validate updated credentials still give access to the configured bike."""
        errors: dict[str, str] = {}
        try:
            bikes_data = await validate_input(self.hass, data)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if entry.data.get("bike_id") not in [bike["bikeid"] for bike in bikes_data]:
                errors["base"] = "bike_not_found"
        return errors

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Handle reauthentication when the Stromer credentials are no longer valid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for updated username and password."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**entry.data, **user_input}
            errors = await self._async_validate_existing_bike(entry, data)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    probatio.Required(probatio.Secret(CONF_PASSWORD)): str,
                }
            ),
            description_placeholders={"name": entry.title},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the Stromer account details."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**entry.data, **user_input}
            if not user_input.get(CONF_CLIENT_SECRET):
                data.pop(CONF_CLIENT_SECRET, None)
            errors = await self._async_validate_existing_bike(entry, data)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    probatio.Required(probatio.Secret(CONF_PASSWORD)): str,
                    probatio.Required(CONF_CLIENT_ID, default=entry.data[CONF_CLIENT_ID]): str,
                    probatio.Optional(
                        probatio.Secret(CONF_CLIENT_SECRET),
                        description={"suggested_value": entry.data.get(CONF_CLIENT_SECRET)},
                    ): str,
                }
            ),
            description_placeholders={"name": entry.title},
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
