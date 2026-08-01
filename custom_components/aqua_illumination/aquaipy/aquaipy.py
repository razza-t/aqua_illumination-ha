#
#   Copyright 2018 Stephen Mc Gowan <mcclown@gmail.com>
#   Modernized for HA 2026.3 / Python 3.14 by Rasmus Tornefrost 
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Module for working with the AquaIllumination range of lights."""

import asyncio
from enum import Enum
import json
import aiohttp

# FIX 1: Use relative imports for vendoring
from .error import ConnError, FirmwareError, MustBeParentError

MIN_SUPPORTED_AI_FIRMWARE_VERSION = "2.0.0"
MAX_SUPPORTED_AI_FIRMWARE_VERSION = "2.5.1"

# FIX 2: Replaced deleted distutils with native version parsing
def _parse_version(version_string):
    """Safely convert a semantic version string to a tuple for comparison."""
    try:
        return tuple(map(int, version_string.split(".")))
    except ValueError:
        return (0, 0, 0)

class Response(Enum):
    """Response codes, for the AquaIPy methods."""
    Success = 0
    Error = 1
    NoSuchColour = 2
    InvalidBrightnessValue = 3
    PowerLimitExceeded = 4
    AllColorsMustBeSpecified = 5
    InvalidData = 6

class HDDevice:
    """A class for handling the conversion of data for a device."""

    def __init__(self, raw_data, primary_mac_address=None):
        self._primary_mac_address = primary_mac_address
        self._mac_address = raw_data['serial_number']
        self._mw_norm = {}
        self._mw_hd = {}
        self._max_mw = 0

        for color, value in raw_data["normal"].items():
            self._mw_norm[color] = value

        for color, value in raw_data["hd"].items():
            self._mw_hd[color] = value

        self._max_mw = raw_data["max_power"]

    @property
    def is_primary(self):
        return self._primary_mac_address == self._mac_address

    @property
    def mac_address(self):
        return self._mac_address

    @property
    def max_mw(self):
        return self._max_mw

    def convert_to_intensity(self, color, percentage):
        if percentage < 0:
            raise ValueError("Percentage must be greater than 0")
        elif 0 <= percentage <= 100:
            return round(percentage * 10)
        else:
            max_percentage = ((self._mw_hd[color]) / self._mw_norm[color]) * 100
            if percentage > max_percentage:
                raise ValueError(f"Percentage for {color} must be between 0 and {max_percentage}")

            hd_percentage = percentage - 100
            hd_brightness_value = (hd_percentage / (max_percentage - 100)) * 1000
            return round(hd_brightness_value + 1000)

    def convert_to_percentage(self, color, intensity):
        if intensity < 0 or intensity > 2000:
            raise ValueError("intensity must be between 0 and 2000")
        elif intensity <= 1000:
            return intensity/10
        else:
            max_hd_percentage = (self._mw_hd[color] - self._mw_norm[color])/self._mw_norm[color]
            hd_in_use = (intensity - 1000) / 1000
            return 100 + (max_hd_percentage * hd_in_use * 100)

    def convert_to_mw(self, color, intensity):
        if intensity < 0 or intensity > 2000:
            raise ValueError("intensity must be between 0 and 2000")
        elif intensity <= 1000:
            return self._mw_norm[color] * (intensity/1000)
        else:
            hd_in_use = (intensity - 1000)/1000
            hd_mw_in_use = hd_in_use * (self._mw_hd[color] - self._mw_norm[color])
            return self._mw_norm[color] + hd_mw_in_use


class AquaIPy:
    """A class that exposes the AquaIllumination Lights API."""

    def __init__(self, name=None, session=None, loop=None):
        self._host = None
        self._base_path = None
        self._mac_addr = None
        self._name = name
        self._product_type = None
        self._firmware_version = None
        self._primary_device = None
        self._other_devices = []

        self._loop = loop
        self._loop_is_local = True

        if self._loop is None:
            try:
                # FIX 3: Updated asyncio loop fetching
                self._loop = asyncio.get_running_loop()
                self._loop_is_local = False
            except RuntimeError:
                self._create_new_event_loop()

        if self._loop.is_closed():
            self._create_new_event_loop()

        if session is None:
            self._session = aiohttp.ClientSession()
            self._session_is_local = True
        else:
            self._session = session
            self._session_is_local = False

    def connect(self, host, check_firmware_support=True):
        return self._loop.run_until_complete(
            self.async_connect(host, check_firmware_support))

    async def async_connect(self, host, check_firmware_support=True):
        self._host = host
        self._base_path = 'http://' + host + '/api'
        await self._async_setup_device_details(check_firmware_support)

    def close(self):
        self._base_path = None

        if self._session_is_local:
            self._loop.run_until_complete(self._session.close())

        if self._loop_is_local:
            self._loop.stop()
            # FIX 4: Updated deprecated all_tasks call
            pending_tasks = asyncio.all_tasks(self._loop)
            self._loop.run_until_complete(asyncio.gather(*pending_tasks))
            self._loop.close()

    @property
    def mac_addr(self):
        return self._mac_addr

    @property
    def name(self):
        return self._name

    @property
    def product_type(self):
        return self._product_type

    @property
    def supported_firmware(self):
        # FIX 5: Uses new tuple-based version check
        current_v = _parse_version(self._firmware_version)
        min_v = _parse_version(MIN_SUPPORTED_AI_FIRMWARE_VERSION)
        max_v = _parse_version(MAX_SUPPORTED_AI_FIRMWARE_VERSION)
        return min_v <= current_v <= max_v

    @property
    def base_path(self):
        return self._base_path

    @property
    def firmware_version(self):
        return self._firmware_version

    def _validate_connection(self):
        if self._base_path is None:
            raise ConnError("Error connecting to host", self._host)

    def _create_new_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop_is_local = True

    async def _async_setup_device_details(self, check_firmware_support):
        r_data = None
        try:
            path = f"{self._base_path}/identity"
            async with self._session.get(path) as resp:
                r_data = await resp.json()
        except Exception:
            self._base_path = None
            raise ConnError("Unable to connect to host", self._host)

        if r_data['response_code'] != 0:
            self._base_path = None
            raise ConnError("Error getting response for device identity", self._host)

        self._mac_addr = r_data['serial_number']
        self._firmware_version = r_data['firmware']
        self._product_type = r_data['product']

        if check_firmware_support and not self.supported_firmware:
            self._base_path = None
            raise FirmwareError("Support is not available for this version of the AquaIllumination firmware yet.", self._firmware_version)

        if r_data['parent'] != "":
            self._base_path = None
            raise MustBeParentError("Connected to non-parent device", r_data['parent'])

        await self._async_get_devices()

    async def _async_get_devices(self):
        path = f"{self._base_path}/power"
        async with self._session.get(path) as resp:
            r_data = await resp.json()
            if r_data['response_code'] != 0:
                self._base_path = None
                raise ConnError("Unable to retrieve device details", self._host)

            self._primary_device = None
            self._other_devices = []

            for device in r_data['devices']:
                temp = HDDevice(device, self.mac_addr)
                if temp.is_primary:
                    self._primary_device = temp
                else:
                    self._other_devices.append(temp)

    async def _async_get_brightness(self):
        self._validate_connection()
        path = f"{self._base_path}/colors"
        async with self._session.get(path) as resp:
            r_data = await resp.json()
            if r_data["response_code"] != 0:
                return Response.Error, None
            del r_data["response_code"]
            return Response.Success, r_data

    async def _async_set_brightness(self, body):
        self._validate_connection()
        path = f"{self._base_path}/colors"
        async with self._session.post(path, json=body) as resp:
            r_data = await resp.json()
            if r_data["response_code"] != 0:
                return Response.Error
            return Response.Success

    def get_schedule_state(self):
        return self._loop.run_until_complete(self.async_get_schedule_state())

    async def async_get_schedule_state(self):
        self._validate_connection()
        path = f"{self._base_path}/schedule/enable"
        async with self._session.get(path) as resp:
            r_data = await resp.json()
            if r_data is None or r_data["response_code"] != 0:
                return None
            return r_data["enable"]

    def set_schedule_state(self, enable):
        return self._loop.run_until_complete(self.async_set_schedule_state(enable))

    async def async_set_schedule_state(self, enable):
        self._validate_connection()
        data = {"enable": enable}
        path = f"{self._base_path}/schedule/enable"
        async with self._session.put(path, data=json.dumps(data)) as resp:
            r_data = await resp.json()
            if r_data is None or r_data['response_code'] != 0:
                return Response.Error
            return Response.Success

    def get_colors(self):
        return self._loop.run_until_complete(self.async_get_colors())

    async def async_get_colors(self):
        colors = []
        resp, data = await self._async_get_brightness()
        if resp != Response.Success:
            return None
        for color in data:
            colors.append(color)
        return colors

    def get_colors_brightness(self):
        return self._loop.run_until_complete(self.async_get_colors_brightness())

    async def async_get_colors_brightness(self):
        colors = {}
        resp_b, brightness = await self._async_get_brightness()
        if resp_b != Response.Success:
            return None
        for color, value in brightness.items():
            colors[color] = self._primary_device.convert_to_percentage(color, value)
        return colors

    def set_colors_brightness(self, colors):
        return self._loop.run_until_complete(self.async_set_colors_brightness(colors))

    async def async_set_colors_brightness(self, colors):
        if len(colors) < len(await self.async_get_colors()):
            return Response.AllColorsMustBeSpecified

        intensities = {}
        mw_value = 0

        for color, value in colors.items():
            intensities[color] = self._primary_device.convert_to_intensity(color, value)
            mw_value += self._primary_device.convert_to_mw(color, intensities[color])

        if mw_value > self._primary_device.max_mw:
            return Response.PowerLimitExceeded

        for device in self._other_devices:
            mw_value = 0
            for color, value in intensities.items():
                mw_value += device.convert_to_mw(color, value)
            if mw_value > device.max_mw:
                return Response.PowerLimitExceeded

        return await self._async_set_brightness(intensities)

    def patch_colors_brightness(self, colors):
        return self._loop.run_until_complete(self.async_patch_colors_brightness(colors))

    async def async_patch_colors_brightness(self, colors):
        if len(colors) < 1:
            return Response.InvalidData

        brightness = await self.async_get_colors_brightness()
        if brightness is None:
            return Response.Error

        for color, value in colors.items():
            brightness[color] = value

        return await self.async_set_colors_brightness(brightness)

    def update_color_brightness(self, color, value):
        return self._loop.run_until_complete(self.async_update_color_brightness(color, value))

    async def async_update_color_brightness(self, color, value):
        if not color:
            return Response.InvalidData
        if value == 0:
            return Response.Success

        brightness = await self.async_get_colors_brightness()
        if brightness is None:
            return Response.Error

        brightness[color] += value
        return await self.async_set_colors_brightness(brightness)
    async def async_get_current_power_draw(self):
        """Calculate the current total power draw in Watts."""
        resp_b, intensities = await self._async_get_brightness()
        if resp_b != Response.Success:
            return 0.0

        total_mw = 0
        # Sum mW for the primary light
        for color, intensity in intensities.items():
            total_mw += self._primary_device.convert_to_mw(color, intensity)
        
        # Sum mW for any linked 'other' devices
        for device in self._other_devices:
            for color, intensity in intensities.items():
                total_mw += device.convert_to_mw(color, intensity)

        # Convert milliwatts to Watts
        return round(total_mw / 1000.0, 2)
