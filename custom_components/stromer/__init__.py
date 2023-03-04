"""Stromer platform for Home Assistant Core."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, LOGGER
from .coordinator import StromerDataUpdateCoordinator
from .stromer import Stromer

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stromer from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Fetch configuration data from config_flow
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data.get(CONF_CLIENT_SECRET, None)

    # Initialize connection to stromer
    stromer = Stromer(username, password, client_id, client_secret)
    await stromer.stromer_connect()
    LOGGER.debug("Stromer entry: {}".format(entry))

    # Use Bike ID as unique id
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=stromer.bike_id)

    # Set up coordinator for fetching data
    coordinator = StromerDataUpdateCoordinator(hass, stromer, SCAN_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator for use in platforms
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Add bike to the HA device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(stromer.bike_id))},
        manufacturer="Stromer",
        name=f"{stromer.bike_name}",
        model=f"{stromer.bike_model}",
    )

    # Set up platforms (i.e. sensors, binary_sensors)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return
