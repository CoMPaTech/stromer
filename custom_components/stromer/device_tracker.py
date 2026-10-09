"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import StromerConfigEntry, StromerDataUpdateCoordinator
from .entity import StromerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: StromerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Stromer sensors from a config entry."""
    coordinator = config_entry.runtime_data

    async_add_entities([StromerTracker(coordinator)], update_before_add=False)


class StromerTracker(StromerEntity, TrackerEntity):
    """Representation of a Device Tracker."""

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self._attr_unique_id = f"{device_id}-location"
        self._attr_name = (f"{coordinator.data.bike_name} Location").lstrip()
        self._attr_device_info: None = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if (latitude := self._coordinator.data.bikedata.get("latitude")) is None:
            return None
        return float(latitude)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if (longitude := self._coordinator.data.bikedata.get("longitude")) is None:
            return None
        return float(longitude)
