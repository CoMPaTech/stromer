"""Stromer platform for Home Assistant Core."""

from datetime import timedelta

import aiodns
import aiohttp
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN, LOGGER
from .coordinator import StromerConfigEntry, StromerDataUpdateCoordinator
from .stromer import ApiError, AuthenticationError, NextLocationError, Stromer

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: StromerConfigEntry) -> bool:
    """Set up Stromer from a config entry."""
    LOGGER.debug(f"Stromer entry: {entry}")

    # Fetch configuration data from config_flow
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data.get(CONF_CLIENT_SECRET, None)

    # Own session (and cookie jar) per entry, HA closes it on unload
    stromer = Stromer(username, password, client_id, client_secret, async_create_clientsession(hass))

    # Setup connection to stromer
    try:
        await stromer.stromer_connect()
    except AuthenticationError as ex:
        raise ConfigEntryAuthFailed(str(ex)) from ex
    except (ApiError, NextLocationError, aiodns.error.DNSError, aiohttp.ClientError, TimeoutError) as ex:
        raise ConfigEntryNotReady(f"Error while connecting to Stromer API: {ex}") from ex

    # Ensure migration from v3 single bike
    if "bike_id" not in entry.data:
        try:
            bikedata = await stromer.stromer_detect()
        except ApiError as ex:
            raise ConfigEntryNotReady(f"Error while detecting bikes: {ex}") from ex
        new_data = {
            **entry.data,
            "bike_id": bikedata[0]["bikeid"],
            "nickname": bikedata[0]["nickname"],
            "model": bikedata[0]["biketype"]
        }
        hass.config_entries.async_update_entry(entry, data=new_data)

    # Set specific bike (instead of all bikes) introduced with morebikes PR
    stromer.bike_id = entry.data["bike_id"]
    stromer.bike_name = entry.data["nickname"]
    stromer.bike_model = entry.data["model"]

    # Use Bike ID as unique id
    if entry.unique_id is None or entry.unique_id == "stromerbike":
        hass.config_entries.async_update_entry(entry, unique_id=f"stromerbike-{stromer.bike_id}")

    # Set up coordinator for fetching data
    coordinator = StromerDataUpdateCoordinator(hass, entry, stromer, SCAN_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Add bike to the HA device registry
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(stromer.bike_id))},
        manufacturer="Stromer",
        name=stromer.bike_name,
        model=stromer.bike_model,
    )

    # Remove non-existing via device
    device_registry.async_update_device(
        device.id,
        name=stromer.bike_name,
        model=stromer.bike_model,
        via_device_id=None,
    )

    # Set up platforms (i.e. sensors, binary_sensors)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: StromerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
