"""Diagnostics support for Stromer."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import StromerConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: StromerConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "bikedata": coordinator.data.bikedata,
        "bike_id": coordinator.data.bike_id,
        "bike_name": coordinator.data.bike_name,
    }
