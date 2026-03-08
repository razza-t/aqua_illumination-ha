from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN # You should define DOMAIN in a const.py or use the string

class AquaIlluminationConfigFlow(config_entries.ConfigFlow, domain="aqua_illumination"):
    """Handle a config flow for Aqua Illumination."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # You could add a check here to see if the IP is valid
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("name"): str,
            }),
            errors=errors,
        )
