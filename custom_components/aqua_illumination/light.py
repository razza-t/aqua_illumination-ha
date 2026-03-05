import logging
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    ColorMode,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt as dt_util

from . import DATA_INDEX, ATTR_LAST_UPDATE

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination light platform."""
    if DATA_INDEX not in hass.data:
        return False

    all_devices = []

    for host, device in hass.data[DATA_INDEX].items():
        if not device.connected:
            raise PlatformNotReady

        # Fetch colors from the parent device
        colors = await device.raw_device.async_get_colors()

        for color in colors:
            all_devices.append(AquaIllumination(device, color))

    add_devices(all_devices)


class AquaIllumination(LightEntity):
    """Representation of an AquaIllumination light channel."""

    # 2026.3 Standard: Explicitly define supported features
    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, light, channel):
        """Initialise the AquaIllumination light."""
        self._light = light
        # Use a cleaner name format
        self._name = channel.replace("_", " ").title()
        self._state = None
        self._brightness = None
        self._channel = channel
        self._unique_id = f"{self._light.mac_addr}_{self._channel}_light"
    
    @property
    def name(self):
        """Return the name of the light."""
        return self._name
    
    @property
    def should_poll(self):
        """Polling is required for local AI devices."""
        return True

    @property
    def is_on(self):
        """Return true if light is on or in schedule mode."""
        return self._state in ['on', 'schedule_mode']

    @property
    def brightness(self):
        """Return the brightness level (0-255)."""
        return self._brightness

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return self._light.attr

    @property
    def available(self):
        """Return if the device is available based on last update."""
        if ATTR_LAST_UPDATE not in self._light.attr:
            return False

        last_update = self._light.attr[ATTR_LAST_UPDATE]
        # Check if last update was within 3x the throttle interval
        return (dt_util.utcnow() - last_update) < (3 * self._light.throttle)

    @property
    def unique_id(self):
        """Return a unique ID for this light channel."""
        return self._unique_id

    async def async_turn_on(self, **kwargs):
        """Turn color channel to given percentage."""
        # Convert HA brightness (0-255) to AI percentage (0-100)
        brightness_pct = (kwargs.get(ATTR_BRIGHTNESS, 255) / 255) * 100
        
        colors_pct = await self._light.raw_device.async_get_colors_brightness()

        # Ensure we don't accidentally push into HD mode over 100% 
        # unless specifically supported in the future.
        for color, val in colors_pct.items():
            if val > 100:
                colors_pct[color] = 100

        colors_pct[self._channel] = brightness_pct

        _LOGGER.debug("Setting %s brightness to %s%%", self._channel, brightness_pct)
        await self._light.raw_device.async_set_colors_brightness(colors_pct)
        await self.async_update()

    async def async_turn_off(self, **kwargs):
        """Turn the specific color channel to 0%."""
        colors_pct = await self._light.raw_device.async_get_colors_brightness()
        colors_pct[self._channel] = 0

        await self._light.raw_device.async_set_colors_brightness(colors_pct)
        await self.async_update()
    
    async def async_update(self):
        """Fetch new state data for this light."""
        await self._light.async_update()
        
        if not self._light.colors_brightness:
            return

        brightness = self._light.colors_brightness.get(self._channel, 0)
        
        if brightness > 0:
            self._state = 'on'
        else:
            self._state = 'off'

        # Update the internal brightness property (0-255)
        self._brightness = (brightness / 100) * 255
