"""Support for Aqua Illumination schedule switches."""
import logging
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aqua Illumination switches from a config entry."""
    # This matches the DATA_INDEX defined in your __init__.py
    DATA_INDEX = "data_" + DOMAIN
    device = hass.data[DATA_INDEX][entry.entry_id]

    # Add the automated schedule toggle
    async_add_entities([AIAutomatedScheduleSwitch(device)], True)


class AIAutomatedScheduleSwitch(SwitchEntity):
    """Representation of the AI light schedule toggle."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, device):
        """Initialize the schedule switch."""
        self._device = device
        self._attr_name = "Scheduled Mode"
        self._attr_unique_id = f"{device.mac_addr}_schedule_switch"
        
        # Link this switch to the main device in the UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.mac_addr)},
            "name": device.name,
            "manufacturer": "Aqua Illumination",
        }

    @property
    def is_on(self):
        """Return true if the light is currently following its internal schedule."""
        return self._device.schedule_state

    @property
    def available(self):
        """Return if the device is reachable."""
        return self._device.connected

    async def async_turn_on(self, **kwargs):
        """Enable internal AI schedule."""
        _LOGGER.debug("Enabling schedule mode for %s", self._device.name)
        await self._device.raw_device.async_set_schedule_state(True)
        # Update the coordinator cache immediately
        await self.async_update()

    async def async_turn_off(self, **kwargs):
        """Disable internal schedule (Manual override)."""
        _LOGGER.debug("Disabling schedule mode for %s", self._device.name)
        await self._device.raw_device.async_set_schedule_state(False)
        # Update the coordinator cache immediately
        await self.async_update()

    async def async_update(self):
        """Fetch latest schedule state."""
        await self._device.async_update()
