"""Stromer Button component for Home Assistant."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import LOGGER
from .coordinator import StromerConfigEntry, StromerDataUpdateCoordinator
from .entity import StromerEntity

BUTTONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="trip_distance",  # (ab)use trip_distance from the bike data to trigger adding button
        translation_key="reset_trip_data",
        device_class=ButtonDeviceClass.RESTART,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: StromerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Stromer Buttons from a config entry."""
    coordinator = config_entry.runtime_data

    entities = []
    for data in coordinator.data.bikedata.items():
        for description in BUTTONS:
            if data[0] == description.key:
                entities.append(StromerButton(coordinator, data, description))
                LOGGER.debug("Add %s %s button", data, description.translation_key)

    async_add_entities(entities, update_before_add=False)


class StromerButton(StromerEntity, ButtonEntity):
    """Representation of a Button."""

    _attr_has_entity_name = True

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        data: tuple[str, Any],
        description: ButtonEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ent = data[0]
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}-bu"

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "trip_distance":
            await self._coordinator.stromer.stromer_reset_trip_data()
