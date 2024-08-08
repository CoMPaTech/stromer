"""Stromer platform for Home Assistant Core."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, LOGGER
from .coordinator import StromerDataUpdateCoordinator
from .stromer import ApiError, Stromer

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Stromer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    LOGGER.debug(f"Stromer entry: {entry}")

    # Fetch configuration data from config_flow
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data.get(CONF_CLIENT_SECRET, None)

    # Initialize module
    stromer = Stromer(username, password, client_id, client_secret)

    # Setup connection to stromer
    try:
        await stromer.stromer_connect()
    except ApiError as ex:
        raise ConfigEntryNotReady("Error while communicating to Stromer API") from ex

    # Remove stale via_device
    if "via_device" in entry.data:
        new_data = {k: v for k, v in entry.data.items() if k != "via_device"}
        hass.config_entries.async_update_entry(entry, data=new_data)

    # Ensure migration from v3 single bike
    if "bike_id" not in entry.data:
        bikedata = stromer.stromer_detect()
        new_data = {**entry.data, "bike_id": bikedata["bikeid"]}
        hass.config_entries.async_update_entry(entry, data=new_data)
        new_data = {**entry.data, "nickname": bikedata["nickname"]}
        hass.config_entries.async_update_entry(entry, data=new_data)
        new_data = {**entry.data, "model": bikedata["biketype"]}
        hass.config_entries.async_update_entry(entry, data=new_data)

    # Set specific bike (instead of all bikes) introduced with morebikes PR
    stromer.bike_id = entry.data["bike_id"]
    stromer.bike_name = entry.data["nickname"]
    stromer.bike_model = entry.data["model"]

    # Use Bike ID as unique id
    if entry.unique_id is None or entry.unique_id == "stromerbike":
        hass.config_entries.async_update_entry(entry, unique_id=f"stromerbike-{stromer.bike_id}")

    # Set up coordinator for fetching data
    coordinator = StromerDataUpdateCoordinator(hass, stromer, SCAN_INTERVAL)  # type: ignore[arg-type]
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

    return unload_ok  # type: ignore [no-any-return]
