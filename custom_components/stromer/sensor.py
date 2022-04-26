"""Stromer Sensor component for Home Assistant."""
from __future__ import annotations

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription,
                                             SensorStateClass)
from homeassistant.const import (LENGTH_KILOMETERS, PERCENTAGE, POWER_WATT,
                                 PRESSURE_BAR, SPEED_KILOMETERS_PER_HOUR,
                                 TEMP_CELSIUS, TIME_SECONDS)
from homeassistant.helpers.entity import EntityCategory

from custom_components.stromer.coordinator import StromerDataUpdateCoordinator
from datetime import datetime, timezone

from .const import DOMAIN
from .entity import StromerEntity

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="assistance_level",
        name="Assistance",
        native_unit_of_measurement=PERCENTAGE,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="atmospheric_pressure",
        name="Pressure (atmosphere)",
        native_unit_of_measurement=PRESSURE_BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_energy_consumption",
        name="Energy used (average)",
        native_unit_of_measurement=POWER_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_speed_total",
        name="Total average",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_speed_trip",
        name="Trip average",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_SOC",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_health",
        name="Battery Condition",
        native_unit_of_measurement=PERCENTAGE,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_temp",
        name="Battery Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="bike_speed",
        name="Bike Speed",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="motor_temp",
        name="Motor Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="power_on_cycles",
        name="Power-on cycles",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="speed",
        name="Speed",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="total_distance",
        name="Total distance",
        native_unit_of_measurement=LENGTH_KILOMETERS,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="total_energy_consumption",
        name="Energy used (total)",
        native_unit_of_measurement=POWER_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="total_time",
        name="Total time",
        native_unit_of_measurement=TIME_SECONDS,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="trip_distance",
        name="Trip distance",
        native_unit_of_measurement=LENGTH_KILOMETERS,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="trip_time",
        name="Trip time",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rcvts",
        name="Last status push",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rcvts_pos",
        name="Last position push",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="timets",
        name="Last position time",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Stromer sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for idx, data in enumerate(coordinator.data.bikedata.items()):
        for description in SENSORS:
            if data[0] == description.key:
                entities.append(StromerSensor(coordinator, idx, data, description))

    async_add_entities(entities, update_before_add=False)


class StromerSensor(StromerEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: StromerDataUpdateCoordinator,
        idx: int,
        data: dict,
        description: SensorEntityDescription,
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

    @staticmethod
    def _ensure_timezone(timestamp: datetime | None) -> datetime | None:
        """Calculate days left until domain expires."""
        if timestamp is None:
            return None

        # If timezone info isn't provided by the Whois, assume UTC.
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)

        return timestamp

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return self._ensure_timezone(datetime.fromtimestamp(int(self._coordinator.data.bikedata.get(self._ent))))

        return self._coordinator.data.bikedata.get(self._ent)
