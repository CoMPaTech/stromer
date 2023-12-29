"""Stromer binary sensor component for Home Assistant."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import StromerDataUpdateCoordinator
from .entity import StromerEntity


@dataclass
class StromerBinarySensorEntityDescription(BinarySensorEntityDescription):  # type: ignore[misc]
    """Describes a Stromer binary sensor entity."""

    icon_off: str | None = None


BINARY_SENSORS: tuple[StromerBinarySensorEntityDescription, ...] = (
    StromerBinarySensorEntityDescription(
        key="light_on",
        translation_key="light_on",
        icon="mdi:lightbulb",
        icon_off="mdi:lightbulb-off",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StromerBinarySensorEntityDescription(
        key="lock_flag",
        translation_key="lock_flag",
        icon="mdi:lock",
        icon_off="mdi:lock-open",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    StromerBinarySensorEntityDescription(
        key="theft_flag",
        translation_key="theft_flag",
        icon="mdi:alarm-light",
        icon_off="mdi:shield-moon",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in BINARY_SENSORS:
            if data[0] == description.key:
                entities.append(
                    StromerBinarySensor(coordinator, idx, data, description)
                )
                LOGGER.debug(
                    "Add %s %s binary_sensor", data, description.translation_key
                )

    async_add_entities(entities, update_before_add=False)


class StromerBinarySensor(StromerEntity, BinarySensorEntity):  # type: ignore[misc]
    """Representation of a Binary Sensor."""

    _attr_has_entity_name = True

    entity_description = StromerBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
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
        return self._coordinator.data.bikedata.get(self._ent)  # type: ignore[no-any-return]
