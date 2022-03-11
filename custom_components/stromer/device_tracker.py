"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.entity import EntityCategory

from custom_components.stromer.coordinator import StromerDataUpdateCoordinator

from .const import DOMAIN
from .entity import StromerEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    longitude = None
    latitude = None
    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        if data[0] == "longitude":
            longitude = data[1]
        if data[0] == "latitude":
            latitude = data[1]
    if longitude and latitude:
        entities.append(StromerTracker(coordinator, longitude, latitude))
        async_add_entities(entities, update_before_add=False)


class StromerTracker(StromerEntity, TrackerEntity):
    """Representation of a Device Tracker."""

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        longitude: float,
        latitude: float,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._latitude = latitude
        self._longitude = longitude

        device_id = coordinator.data.bike_id

        self._attr_unique_id = f"{device_id}-location"
        self._attr_name = (f"{coordinator.data.bike_name} Location").lstrip()
        self._attr_device_info: None = None
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return "gps"

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._longitude
