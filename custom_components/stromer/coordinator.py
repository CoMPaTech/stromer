"""DataUpdateCoordinator for Stromer."""
from typing import Any, NamedTuple

from .stromer import Stromer

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, LOGGER


class StromerData(NamedTuple):
    """Stromer data stored in the DataUpdateCoordinator."""

    bikedata: dict[str, Any]
    bike_id: str
    bike_name: str


class StromerDataUpdateCoordinator(DataUpdateCoordinator[StromerData]):
    """Class to manage fetching Stromer data from single endpoint."""

    def __init__(self, hass: HomeAssistant, stromer: Stromer, interval: float) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=interval)
        self.stromer = stromer

    async def _async_update_data(self) -> StromerData:
        """Fetch data from Stromer."""
        try:
            await self.stromer.stromer_update()

            bike_data = self.stromer.bike
            bike_data.update(self.stromer.status)
            bike_data.update(self.stromer.position)

            data = [bike_data, self.stromer.bike_id, self.stromer.bike_name]
            LOGGER.debug("Stromer data %s updated", data)

        except Exception as err:
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        return StromerData(*data)


class ApiError(BaseException):
    """Error to indicate something wrong with the API."""
