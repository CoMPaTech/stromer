"""DataUpdateCoordinator for Stromer."""
from datetime import timedelta
from typing import Any, NamedTuple

import aiodns
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER
from .stromer import ApiError, AuthenticationError, NextLocationError, Stromer

type StromerConfigEntry = ConfigEntry[StromerDataUpdateCoordinator]


class StromerData(NamedTuple):
    """Stromer data stored in the DataUpdateCoordinator."""

    bikedata: dict[str, Any]
    bike_id: str
    bike_name: str


class StromerDataUpdateCoordinator(DataUpdateCoordinator[StromerData]):
    """Class to manage fetching Stromer data from single endpoint."""

    config_entry: StromerConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: StromerConfigEntry,
        stromer: Stromer,
        interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=interval,
        )
        self.stromer = stromer

    async def _async_update_data(self) -> StromerData:
        """Fetch data from Stromer."""
        try:
            await self.stromer.stromer_update()
        except AuthenticationError as ex:
            raise ConfigEntryAuthFailed(str(ex)) from ex
        except ApiError as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex
        except NextLocationError as ex:
            raise UpdateFailed(f"Error while getting authentication location: {ex}") from ex
        except (aiodns.error.DNSError, aiohttp.ClientError, TimeoutError) as ex:
            raise UpdateFailed(f"Error connecting to Stromer API: {ex}") from ex

        # Rewrite position["rcvts"] as this key exists in status
        if "rcvts" in self.stromer.position:
            self.stromer.position["rcvts_pos"] = self.stromer.position.pop("rcvts")

        bike_data = self.stromer.bike
        bike_data.update({"bike_model": self.stromer.bike_model, "bike_name": self.stromer.bike_name})
        bike_data.update(self.stromer.status)
        bike_data.update(self.stromer.position)

        LOGGER.debug("Stromer data %s updated", bike_data)
        return StromerData(bike_data, self.stromer.bike_id, self.stromer.bike_name)  # type: ignore[arg-type]
