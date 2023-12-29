"""Stromer Switch component for Home Assistant."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import StromerDataUpdateCoordinator
from .entity import StromerEntity

SWITCHES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="lock_flag",
        translation_key="lock",
        icon="mdi:lock",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="light_on",
        translation_key="light",
        icon="mdi:light-flood-down",
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Stromer Switches from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in SWITCHES:
            if data[0] == description.key:
                entities.append(StromerSwitch(coordinator, idx, data, description))
                LOGGER.debug("Add %s %s switch", data, description.translation_key)

    async_add_entities(entities, update_before_add=False)


class StromerSwitch(StromerEntity, SwitchEntity):  # type: ignore[misc]
    """Representation of a Switch."""

    _attr_has_entity_name = True

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
        description: SwitchEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ent = data[0]
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}-sw"

    @callback  # type: ignore[misc]
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self._coordinator.data.bikedata.get(self._ent)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        if self.entity_description.key == "lock_flag":
            await self._coordinator.stromer.stromer_call_lock(True)
        if self.entity_description.key == "light_on":
            await self._coordinator.stromer.stromer_call_light("on")
        # Call update on the bike so `is_on` correctly reflects status
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        if self.entity_description.key == "lock_flag":
            await self._coordinator.stromer.stromer_call_lock(False)
        if self.entity_description.key == "light_on":
            await self._coordinator.stromer.stromer_call_light("off")
        # Call update on the bike so `is_on` correctly reflects status
        await self._coordinator.async_request_refresh()
