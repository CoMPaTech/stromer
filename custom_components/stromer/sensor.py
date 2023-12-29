"""Stromer Sensor component for Home Assistant."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import StromerDataUpdateCoordinator
from .entity import StromerEntity

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="assistance_level",
        translation_key="assistance_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="atmospheric_pressure",
        translation_key="atmospheric_pressure",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_energy_consumption",
        translation_key="average_energy_consumption",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="average_speed_total",
        translation_key="average_speed_total",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_speed_trip",
        translation_key="average_speed_trip",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_SOC",
        translation_key="battery_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_health",
        translation_key="battery_health",
        native_unit_of_measurement=PERCENTAGE,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_temp",
        translation_key="battery_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="bike_speed",
        translation_key="bike_speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="motor_temp",
        translation_key="motor_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="power_on_cycles",
        translation_key="power_on_cycles",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="speed",
        translation_key="speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="total_distance",
        translation_key="total_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="total_energy_consumption",
        translation_key="total_energy_consumption",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="total_time",
        translation_key="total_time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="trip_distance",
        translation_key="trip_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="trip_time",
        translation_key="trip_time",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rcvts",
        translation_key="rcvts",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rcvts_pos",
        translation_key="rcvts_pos",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="timets",
        translation_key="timets",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in SENSORS:
            if data[0] == description.key:
                entities.append(StromerSensor(coordinator, idx, data, description))
                LOGGER.debug("Add %s %s sensor", data, description.translation_key)

    async_add_entities(entities, update_before_add=False)


class StromerSensor(StromerEntity, SensorEntity):  # type: ignore[misc]
    """Representation of a Sensor."""

    _attr_has_entity_name = True

    entity_description = SensorEntityDescription

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
        description: SensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ent = data[0]
        self._coordinator = coordinator

        device_id = coordinator.data.bike_id

        self.entity_description = description
        self._attr_unique_id = f"{device_id}-{description.key}"

    @staticmethod
    def _ensure_timezone(timestamp: datetime | None) -> datetime | None:
        """Calculate days left until domain expires."""
        if timestamp is None:
            return None

        # If timezone info isn't provided by the Whois, assume UTC.
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)

        return timestamp

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return self._ensure_timezone(
                datetime.fromtimestamp(
                    int(self._coordinator.data.bikedata.get(self._ent))
                )
            )

        return self._coordinator.data.bikedata.get(self._ent)
