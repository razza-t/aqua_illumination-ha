import logging
import voluptuous as vol

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.exceptions import PlatformNotReady
from homeassistant.util import dt as dt_util

from . import DATA_INDEX, ATTR_LAST_UPDATE

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AquaIllumination switch platform."""
    if DATA_INDEX not in hass.data:
        return False

    all_devices = []

    for host, device in hass.data[DATA_INDEX].items():
        if not device.connected:
            raise PlatformNotReady

        # This switch controls whether the light follows its internal schedule
        all_devices.append(AIAutomatedScheduleSwitch(device))

    add_devices(all_devices)


class AIAutomatedScheduleSwitch(SwitchEntity):
    """Representation of AI light schedule switch."""

    # 2026.3 Standard: Explicitly define the entity's behavior using Enums
    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, device):
        """Initialise the AI switch."""
        self._device = device
        # The name will appear as "Aqua Illumination Scheduled Mode"
        self._attr_name = "Scheduled Mode"
        self._state = None
        self._attr_unique_id = f"{self._device.mac_addr}_schedule_switch"
    
    @property
    def should_poll(self):
        """Polling is required to keep the toggle in sync with the physical light."""
        return True

    @property
    def is_on(self):
        """Return true if scheduled mode is enabled."""
        return self._state 

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return self._device.attr

    @property
    def available(self):
        """Return if the device is available."""
        if ATTR_LAST_UPDATE not in self._device.attr:
            return False

        last_update = self._device.attr[ATTR_LAST_UPDATE]
        # Uses the .throttle property added to AIData in __init__.py
        return (dt_util.utcnow() - last_update) < (3 * self._device.throttle)

    async def async_turn_on(self, **kwargs):
        """Enable schedule mode."""
        _LOGGER.debug("Enabling schedule mode for %s", self._device.name)
        await self._device.raw_device.async_set_schedule_state(True)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Disable schedule mode (Manual control)."""
        _LOGGER.debug("Disabling schedule mode for %s", self._device.name)
        await self._device.raw_device.async_set_schedule_state(False)
        self._state = False
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for scheduled mode."""
        await self._device.async_update()
        self._state = self._device.schedule_state
