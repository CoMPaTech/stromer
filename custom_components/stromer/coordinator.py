"""DataUpdateCoordinator for Stromer."""
from typing import Any, NamedTuple

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER
from .stromer import ApiError, Stromer


class StromerData(NamedTuple):
    """Stromer data stored in the DataUpdateCoordinator."""

    bikedata: dict[str, Any]
    bike_id: str
    bike_name: str


class StromerDataUpdateCoordinator(DataUpdateCoordinator[StromerData]):  # type: ignore[misc]
    """Class to manage fetching Stromer data from single endpoint."""

    def __init__(self, hass: HomeAssistant, stromer: Stromer, interval: float) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=interval)
        self.stromer = stromer

    async def _async_update_data(self) -> StromerData:
        """Fetch data from Stromer."""
        try:
            await self.stromer.stromer_update()

            # Rewrite position["rcvts"] as this key exists in status
            if "rcvts" in self.stromer.position:
                self.stromer.position["rcvts_pos"] = self.stromer.position.pop("rcvts")

            bike_data = self.stromer.bike
            bike_data.update(self.stromer.status)
            bike_data.update(self.stromer.position)

            data = [bike_data, self.stromer.bike_id, self.stromer.bike_name]
            LOGGER.debug("Stromer data %s updated", data)

        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise ConfigEntryAuthFailed from err
        return StromerData(*data)  # type: ignore [arg-type]
