"""The AquaIllumination Light component"""
from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle, dt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aqua Illumination from a UI config entry."""
        if DATA_INDEX not in hass.data:
                hass.data[DATA_INDEX] = {}

                    host = entry.data.get("host")
                        name = entry.data.get("name")

                            # Initialize your device
                                device = AIData(host, name, SCAN_INTERVAL)
                                    await device.async_update()
                                        
                                            # Store the device using the unique entry_id
                                                hass.data[DATA_INDEX][entry.entry_id] = device

                                                    # Forward the setup to the platforms (light, switch, sensor)
                                                        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

                                                            return True

                                                            async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
                                                                """Unload a config entry (when you delete it from the UI)."""
                                                                    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
                                                                        if unload_ok:
                                                                                hass.data[DATA_INDEX].pop(entry.entry_id)

                                                                                    return unload_ok

_LOGGER = logging.getLogger(__name__)

ATTR_LAST_UPDATE = 'last_update'
DOMAIN = 'aqua_illumination'
DATA_INDEX = "data_" + DOMAIN

# 2026.3 Standard: Explicitly define platforms
PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(
        cv.ensure_list, [vol.Schema({
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_NAME): cv.string
        })]
    )
}, extra=vol.ALLOW_EXTRA)

SCAN_INTERVAL = timedelta(seconds=10)

async def async_setup(hass, hass_config):
    """Setup the AquaIllumination component"""
    if DATA_INDEX not in hass.data:
        hass.data[DATA_INDEX] = {}

    conf = hass_config.get(DOMAIN)
    if conf is None:
        return True

    for config in conf:
        await _async_setup_ai_device(hass, hass_config, config)

    # Modern discovery loop: Awaiting directly ensures setup finishes predictably
    for platform in PLATFORMS:
        await discovery.async_load_platform(hass, platform, DOMAIN, {}, hass_config)

    return True

async def _async_setup_ai_device(hass, hass_config, config):
    """Setup an individual device"""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    if host in hass.data[DATA_INDEX]:
        return

    # Setup connection with devices
    device = AIData(host, name, SCAN_INTERVAL)
    
    await device.async_update()
    hass.data[DATA_INDEX][host] = device


class AIData:
    """Class for handling data from AI devices and caching."""

    def __init__(self, host, name, throttle):
        # PATCH: Use local import for bundled library
        from .aquaipy import AquaIPy

        self.attr = {}
        self._connected = False
        self._device = AquaIPy(name)
        self._t = throttle
        self._colors_brightness = None
        self._schedule_state = None
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
    def throttle(self):
        """Return the throttle interval."""
        return self._t

    async def _async_update(self):
        if not self.connected:
            # PATCH: Use local import for error handling
            from .aquaipy.error import FirmwareError, ConnError, MustBeParentError
            
            try:
                await self._device.async_connect(self._host)
            except FirmwareError:
                _LOGGER.error("Invalid firmware version for AI device: %s", self.name)
                return
            except ConnError:
                _LOGGER.error("Unable to connect to AI device at %s", self._host)
                return
            except MustBeParentError:
                _LOGGER.error("The device at %s must be the parent light. Verify pairings.", self._host)
                return

            self._connected = True
            
        self._colors_brightness = await self._device.async_get_colors_brightness()
        self._schedule_state = await self._device.async_get_schedule_state()

        # Update last seen timestamp
        self.attr[ATTR_LAST_UPDATE] = dt.utcnow()
    async def async_setup_entry(hass, entry):
        """Set up Aqua Illumination from a config entry."""
        host = entry.data["host"]
        name = entry.data["name"]

        # Initialize your AIData class (same as before)
        device = AIData(host, name, SCAN_INTERVAL)
        await device.async_update()
    
        hass.data[DATA_INDEX][entry.entry_id] = device

        # Forward the setup to the platforms (light, sensor, switch)
        for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
        return True
