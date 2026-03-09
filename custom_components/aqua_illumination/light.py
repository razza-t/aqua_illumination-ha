"""Support for Aqua Illumination light channels."""
import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
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
    """Set up Aqua Illumination lights from a config entry."""
    # Matches the DATA_INDEX in your __init__.py
    DATA_INDEX = "data_" + DOMAIN
    device = hass.data[DATA_INDEX][entry.entry_id]

    # Fetch colors from the parent hardware
    colors = await device.raw_device.async_get_colors()

    entities = []
    for color in colors:
        entities.append(AquaIlluminationLight(device, color))

    async_add_entities(entities, True)


class AquaIlluminationLight(LightEntity):
    """Representation of an individual LED color channel as a light."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, device, channel):
        """Initialise the light channel."""
        self._device = device
        self._channel = channel
        
        # Clean up name (e.g., "royal_blue" -> "Royal Blue")
        self._attr_name = channel.replace("_", " ").title()
        self._attr_unique_id = f"{device.mac_addr}_{channel}_light"
        
        # Group this light under the main device in the UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.mac_addr)},
            "name": device.name,
            "manufacturer": "Aqua Illumination",
        }

    @property
    def is_on(self):
        """Return true if this specific channel has any brightness."""
        brightness = self._device.colors_brightness.get(self._channel, 0) if self._device.colors_brightness else 0
        return brightness > 0

    @property
    def brightness(self):
        """Return the brightness level (0-255)."""
        if self._device.colors_brightness and self._channel in self._device.colors_brightness:
            # Convert AI percentage (0-100) to HA brightness (0-255)
            return (self._device.colors_brightness[self._channel] / 100) * 255
        return 0

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return self._device.attr

    @property
    def available(self):
        """Return if the device is reachable."""
        return self._device.connected

    async def async_turn_on(self, **kwargs):
        """Turn color channel to given percentage."""
        target_brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        if target_brightness is None:
            # If no brightness sent, restore previous or go to 100%
            current_br = self.brightness
            target_brightness = current_br if current_br > 0 else 255

        # HA 0-255 -> AI 0-100
        brightness_pct = (target_brightness / 255) * 100
        
        # Get all channels to update only the current one
        colors_pct = await self._device.raw_device.async_get_colors_brightness()
        colors_pct[self._channel] = brightness_pct

        await self._device.raw_device.async_set_colors_brightness(colors_pct)
        await self.async_update()

    async def async_turn_off(self, **kwargs):
        """Turn the specific color channel to 0%."""
        colors_pct = await self._device.raw_device.async_get_colors_brightness()
        colors_pct[self._channel] = 0

        await self._device.raw_device.async_set_colors_brightness(colors_pct)
        await self.async_update()
    
    async def async_update(self):
        """Fetch new state data for this light."""
        await self._device.async_update()
