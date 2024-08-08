"""Generic Stromer Entity Class."""
from __future__ import annotations

from typing import Any

from homeassistant.const import ATTR_NAME, ATTR_VIA_DEVICE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StromerData, StromerDataUpdateCoordinator


class StromerEntity(CoordinatorEntity[StromerData]):  # type:ignore [misc]
    """Represent a Stromer Entity."""

    coordinator: StromerDataUpdateCoordinator

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
    ) -> None:
        """Initialise the gateway."""
        super().__init__(coordinator)

        configuration_url: str | None = None

        data = coordinator.data.bikedata

        self._attr_device_info = DeviceInfo(
            configuration_url=configuration_url,
            identifiers={(DOMAIN, str(coordinator.data.bike_id))},
            manufacturer="Stromer",
            model=data.get("bikemodel"),
            name=data.get("nickname"),
            sw_version=data.get("suiversion"),
            hw_version=data.get("tntversion"),
        )

        self._attr_device_info.update(
            {
                ATTR_NAME: data.get("nickname"),
                ATTR_VIA_DEVICE: None,
            }
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available  # type: ignore[no-any-return]

    @property
    def device(self) -> dict[str, Any]:
        """Return data for this device."""
        return self.coordinator.data.bike_id  # type: ignore[no-any-return]

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates."""
        self._handle_coordinator_update()
        await super().async_added_to_hass()
