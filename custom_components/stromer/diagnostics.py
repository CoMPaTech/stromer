"""Diagnostics support for Stromer."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import StromerDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: StromerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "bikedata": coordinator.data.bikedata,
        "bike_id": coordinator.data.bike_id,
        "bike_name": coordinator.data.bike_name,
    }
