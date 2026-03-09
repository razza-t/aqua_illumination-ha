"""Support for Aqua Illumination sensors."""
import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqua Illumination sensors from a config entry."""
    # This matches the DATA_INDEX in your __init__.py
    DATA_INDEX = "data_" + DOMAIN
    device = hass.data[DATA_INDEX][entry.entry_id]

    # Initialize the basic diagnostic sensors
    entities = [
        AIDiagnosticSensor(device, "Firmware Version", "firmware"),
        AIDiagnosticSensor(device, "Connection Status", "connection"),
    ]

    # Fetch the available LED color channels from the hardware
    colors = await device.raw_device.async_get_colors()
    if colors:
        for color in colors:
            entities.append(AIChannelBrightnessSensor(device, color))

    async_add_entities(entities, True)


class AIChannelBrightnessSensor(SensorEntity):
    """Representation of an individual LED channel brightness %."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:brightness-percent"

    def __init__(self, device, channel):
        """Initialize the channel sensor."""
        self._device = device
        self._channel = channel
        
        # Clean up name (e.g., "deep_blue" -> "Deep Blue Brightness")
        clean_name = channel.replace('_', ' ').title()
        self._attr_name = f"{clean_name} Brightness"
        
        self._attr_unique_id = f"{device.mac_addr}_{channel}_brightness_sensor"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.mac_addr)},
            "name": device.name,
            "manufacturer": "Aqua Illumination",
        }

    @property
    def extra_state_attributes(self):
        """Return device-specific attributes."""
        return self._device.attr

    @property
    def native_value(self):
        """Return the current percentage."""
        if self._device.colors_brightness and self._channel in self._device.colors_brightness:
            return round(float(self._device.colors_brightness[self._channel]), 2)
        return None

    async def async_update(self) -> None:
        """Fetch new state data."""
        await self._device.async_update()


class AIDiagnosticSensor(SensorEntity):
    """Firmware and Connection status sensors."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, name, sensor_type):
        self._device = device
        self._type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{device.mac_addr}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.mac_addr)},
            "name": device.name,
        }

    @property
    def native_value(self):
        if self._type == "firmware":
            return self._device.raw_device.firmware_version
        if self._type == "connection":
            return "Connected" if self._device.connected else "Disconnected"
        return None
