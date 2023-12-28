"""Stromer Switch component for Home Assistant."""
from __future__ import annotations
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)


from custom_components.stromer.coordinator import StromerDataUpdateCoordinator

from .const import DOMAIN
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
        icon="mdi:light",
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromer Switches from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in SWITCHES:
            if data[0] == description.key:
                entities.append(StromerSwitch(coordinator, idx, data, description))

    async_add_entities(entities, update_before_add=False)


class StromerSwitch(StromerEntity, SwitchEntity):
    """Representation of a Switch."""

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
        description: SwitchEntityDescription,
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

    # Not working yet
    # @property
    # def is_on(self) -> bool:
    #    """Return True if entity is on."""
    #    return self.device["switches"][self.entity_description.key]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        if self.entity_description.key == "lock_flag":
            await self._coordinator.stromer.stromer_call_lock(True)
        if self.entity_description.key == "light_on":
            await self._coordinator.stromer.stromer_call_light("on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        if self.entity_description.key == "lock_flag":
            await self._coordinator.stromer.stromer_call_lock(False)
        if self.entity_description.key == "light_on":
            await self._coordinator.stromer.stromer_call_light("off")
