"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations
from custom_components.stromer.coordinator import StromerDataUpdateCoordinator


from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory


from .const import DOMAIN
from .entity import StromerEntity


BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="light_on",
        name="Light on",
        entity_category=EntityCategory.LIGHT,
    ),
    BinarySensorEntityDescription(
        key="lock_flag",
        name="Bike Lock",
        entity_category=EntityCategory.LOCK,
    ),
    BinarySensorEntityDescription(
        key="theft_flag",
        name="Theft flag",
        entity_category=EntityCategory.TAMPER,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in BINARY_SENSORS:
            if data[0] == description.key:
                entities.append(StromerBinarySensor(coordinator, idx, data, description))

    async_add_entities(entities, update_before_add=False)


class StromerBinarySensor(StromerEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
        description: BinarySensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._idx = idx
        self._ent = data[0]
        self._data = data[1]

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}"
        self._attr_name = (f"{coordinator.data.bike_name} {description.name}").lstrip()

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._data
