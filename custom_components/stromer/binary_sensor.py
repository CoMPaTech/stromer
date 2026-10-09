"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import LOGGER
from .coordinator import StromerConfigEntry, StromerDataUpdateCoordinator
from .entity import StromerEntity

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="light_on",
        translation_key="light_on",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="lock_flag",
        translation_key="lock_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="theft_flag",
        translation_key="theft_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: StromerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Stromer sensors from a config entry."""
    coordinator = config_entry.runtime_data

    entities = []
    for data in coordinator.data.bikedata.items():
        for description in BINARY_SENSORS:
            if data[0] == description.key:
                entities.append(StromerBinarySensor(coordinator, data, description))
                LOGGER.debug(
                    "Add %s %s binary_sensor", data, description.translation_key
                )

    async_add_entities(entities, update_before_add=False)


class StromerBinarySensor(StromerEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    _attr_has_entity_name = True

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        data: tuple[str, Any],
        description: BinarySensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ent = data[0]
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._coordinator.data.bikedata.get(self._ent)
