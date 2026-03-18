import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

# FIX: Import the library from your new vendored folder
from .aquaipy.aquaipy import AquaIPy
from .aquaipy.error import ConnError
from .const import DOMAIN

class AquaIlluminationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aqua Illumination."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user enters IP and Name."""
        errors = {}

        if user_input is not None:
            host = user_input["host"]
            name = user_input["name"]

            # Validate the connection before allowing the entry to be created
            try:
                ai = AquaIPy()
                # We use a timeout to prevent the UI from hanging if IP is wrong
                await ai.async_connect(host)
                
                # Check if this serial number (MAC) is already configured
                await self.async_set_unique_id(ai.mac_addr)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=name, 
                    data={
                        "host": host,
                        "name": name,
                    }
                )
            except ConnError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("name"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Standard options flow handler (required for 2026.3)."""
        return AquaIlluminationOptionsFlowHandler(config_entry)

class AquaIlluminationOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the integration (e.g., changing IP later)."""
    
def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # This line handles the assignment for you in a safe way:
        super().__init__(config_entry)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(
                    "host",
                    default=self.config_entry.data.get("host"),
                ): str,
            }),
        )
