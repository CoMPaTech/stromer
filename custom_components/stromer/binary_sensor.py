"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity, BinarySensorEntityDescription)
from homeassistant.helpers.entity import EntityCategory

from custom_components.stromer.coordinator import StromerDataUpdateCoordinator

from .const import DOMAIN
from .entity import StromerEntity


@dataclass
class StromerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Stromer binary sensor entity."""

    icon_off: str | None = None


BINARY_SENSORS: tuple[StromerBinarySensorEntityDescription, ...] = (
    StromerBinarySensorEntityDescription(
        key="light_on",
        name="Light on",
        icon="mdi:lightbulb",
        icon_off="mdi:lightbulb-off",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StromerBinarySensorEntityDescription(
        key="lock_flag",
        name="Bike Lock",
        icon="mdi:lock",
        icon_off="mdi:lock-open",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StromerBinarySensorEntityDescription(
        key="theft_flag",
        name="Theft flag",
        icon="mdi:alarm-light",
        icon_off="mdi:shield-moon",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in BINARY_SENSORS:
            if data[0] == description.key:
                entities.append(
                    StromerBinarySensor(coordinator, idx, data, description)
                )

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
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}"
        self._attr_name = (f"{coordinator.data.bike_name} {description.name}").lstrip()

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._coordinator.data.bikedata.get(self._ent)
