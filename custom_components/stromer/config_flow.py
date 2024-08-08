"""Config flow for Stromer integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import BIKE_DETAILS, CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, LOGGER
from .stromer import Stromer

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Optional(CONF_CLIENT_SECRET): str,
    }
)


async def validate_input(_: HomeAssistant, data: dict[str, Any]) -> dict:
    """Validate the user input allows us to connect by returning a dictionary with all bikes under the account."""
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    client_id = data[CONF_CLIENT_ID]
    client_secret = data.get(CONF_CLIENT_SECRET, None)

    # Initialize connection to stromer
    stromer = Stromer(username, password, client_id, client_secret)
    if not await stromer.stromer_connect():
        raise InvalidAuth

    # All bikes information available
    all_bikes = await stromer.stromer_detect()

    return all_bikes


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg, misc]
    """Handle a config flow for Stromer."""

    VERSION = 1

    async def async_step_bike(
        self, user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle selecting bike step."""
        if user_input is None:
            STEP_BIKE_DATA_SCHEMA = vol.Schema(
                { vol.Required(BIKE_DETAILS): vol.In(list(self.friendly_names)), }
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

        LOGGER.info(f"Using {selected_bike} (i.e. bike ID {bike_id} to talk to the Stromer API")

        await self.async_set_unique_id(f"stromerbike-{bike_id}")
        self._abort_if_unique_id_configured()

        LOGGER.info(f"Creating entry using {nickname} as bike device name")
        return self.async_create_entry(title=nickname, data=self.user_input_data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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


class CannotConnect(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
