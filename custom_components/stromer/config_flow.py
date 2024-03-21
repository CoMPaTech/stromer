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
    """Validate the user input allows us to connect."""
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    client_id = data[CONF_CLIENT_ID]
    client_secret = data.get(CONF_CLIENT_SECRET, None)

    # Initialize connection to stromer
    stromer = Stromer(username, password, client_id, client_secret)
    if not await stromer.stromer_connect():
        raise InvalidAuth

    bikes_data = await stromer.stromer_detect()

    # Return info that you want to store in the config entry.
    return bikes_data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg, misc]
    """Handle a config flow for Stromer."""

    VERSION = 1

    async def async_step_bike(
        self, user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle selecting bike step."""
        if user_input is None:
            STEP_BIKE_DATA_SCHEMA = vol.Schema(
                { vol.Required(BIKE_DETAILS): vol.In(self.bikes), }
            )
            log = f"bikes = {self.bikes}"
            LOGGER.debug(log)
            LOGGER.debug("calling show form on bike")
            return self.async_show_form(
                step_id="bike", data_schema=STEP_BIKE_DATA_SCHEMA
            )

        # log = f"Completed bike selection = {user_input}"
        # LOGGER.debug(log)
        bike_data = user_input[BIKE_DETAILS].split(":")
        self.user_input_data["bike_id"] = bike_data[0]
        self.user_input_data["nickname"] = bike_data[1]
        self.user_input_data["model"] = bike_data[2]
        log = f"Completed bike data = {self.user_input_data}"

        LOGGER.debug("processing")

        await self.async_set_unique_id(f"stromerbike-{self.user_input_data['bike_id']}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=self.user_input_data["nickname"], data=self.user_input_data)

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
            # Handle single bike as multi-bike
            self.bikes = []
            for bike in bikes_data:
               self.bikes.append(f"{bike['bikeid']}:{bike['nickname']}:{bike['biketype']}")

            # Save account info
            self.user_input_data = user_input
            # log = f"User input: {user_input}"
            # LOGGER.debug(log)
            log = f"Bikes: {self.bikes}"
            LOGGER.debug(log)
            # Display available bikes
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
