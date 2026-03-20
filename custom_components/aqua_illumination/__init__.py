"""The AquaIllumination Light component."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle, dt

# Internal Imports
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_LAST_UPDATE = 'last_update'
DATA_INDEX = f"data_{DOMAIN}"

# 2026.3 Standard: Explicitly define platforms
PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.SENSOR]
SCAN_INTERVAL = timedelta(seconds=10)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component. This is required for the integration to index properly."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aqua Illumination from a UI config entry."""
    hass.data.setdefault(DATA_INDEX, {})

    host = entry.data.get("host")
    name = entry.data.get("name")

    # Initialize the data coordinator
    device = AIData(host, name, SCAN_INTERVAL)
    await device.async_update()
    
    # Store the device using the unique entry_id
    hass.data[DATA_INDEX][entry.entry_id] = device

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DATA_INDEX].pop(entry.entry_id, None)
    return unload_ok

class AIData:
    """Class for handling data from AI devices and caching."""

    def __init__(self, host, name, throttle):
        # Local import to prevent startup circular dependencies
        from .aquaipy.aquaipy import AquaIPy

        self.attr = {}
        self._connected = False
        self._device = AquaIPy(name)
        self._t = throttle
        self._colors_brightness = None
        self._schedule_state = None
        self._power_draw = 0.0
        self._host = host

        self.async_update = Throttle(throttle)(self._async_update)

    @property
    def name(self):
        return self._device.name

    @property
    def mac_addr(self):
        return self._device.mac_addr
    
    @property
    def connected(self):
        return self._connected

    @property
    def colors_brightness(self):
        return self._colors_brightness

    @property
    def raw_device(self):
        return self._device

    @property
    def schedule_state(self):
        return self._schedule_state

    @property
    def power_draw(self):
        """Return the current calculated power draw."""
        return self._power_draw

    async def _async_update(self):
        """Fetch the latest data from the device."""
        if not self._connected:
            from .aquaipy.error import FirmwareError, ConnError, MustBeParentError
            
            try:
                await self._device.async_connect(self._host)
                self._connected = True
            except FirmwareError:
                _LOGGER.error("Invalid firmware version for AI device: %s", self.name)
                return
            except ConnError:
                _LOGGER.error("Unable to connect to AI device at %s", self._host)
                return
            except MustBeParentError:
                _LOGGER.error("The device at %s must be the parent light.", self._host)
                return
            
        # Update all values in one cycle
        self._colors_brightness = await self._device.async_get_colors_brightness()
        self._schedule_state = await self._device.async_get_schedule_state()
        
        # New: Get the power draw calculation from aquaipy
        self._power_draw = await self._device.async_get_current_power_draw()
        
        self.attr[ATTR_LAST_UPDATE] = dt.utcnow()
