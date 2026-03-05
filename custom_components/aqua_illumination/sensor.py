import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.exceptions import PlatformNotReady
from homeassistant.util import dt as dt_util

from . import DATA_INDEX, ATTR_LAST_UPDATE

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the AquaIllumination sensor platform."""
    if DATA_INDEX not in hass.data:
        return False

    all_entities = []

    for host, device in hass.data[DATA_INDEX].items():
        if not device.connected:
            raise PlatformNotReady

        # Fetch the available color channels
        colors = await device.raw_device.async_get_colors()

        for color in colors:
            all_entities.append(AquaIlluminationChannelBrightness(device, color))

    add_entities(all_entities)


class AquaIlluminationChannelBrightness(SensorEntity):
    """Representation of an AquaIllumination light channel brightness sensor."""

    # 2026.3 Standards: Define behavior via attributes
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, channel):
        """Initialise the AI brightness sensor."""
        self._device = device
        self._channel = channel
        # Format name as "Deep Blue Brightness"
        self._attr_name = f"{channel.replace('_', ' ').title()} Brightness"
        self._attr_unique_id = f"{self._device.mac_addr}_{channel}_sensor"
        self._attr_native_value = None

    @property
    def should_poll(self):
        """Polling required to stay in sync with the hardware."""
        return True

    @property
    def icon(self):
        """Dynamic icon for brightness."""
        return "mdi:brightness-percent"

    @property
    def extra_state_attributes(self):
        """Return the device attributes."""
        return self._device.attr

    @property
    def available(self):
        """Return if the device is reachable."""
        if ATTR_LAST_UPDATE not in self._device.attr:
            return False

        last_update = self._device.attr[ATTR_LAST_UPDATE]
        # Allow a 3x window of the scan interval before marking unavailable
        return (dt_util.utcnow() - last_update) < (3 * self._device.throttle)

    async def async_update(self):
        """Fetch the latest brightness percentage for this channel."""
        await self._device.async_update()
        
        if self._device.colors_brightness and self._channel in self._device.colors_brightness:
            brightness = self._device.colors_brightness[self._channel]
            # Store as float with 2 decimal places
            self._attr_native_value = round(float(brightness), 2)
