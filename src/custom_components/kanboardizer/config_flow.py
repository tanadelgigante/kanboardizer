"""Config flow for Kanboard integration."""
from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_API_TOKEN

import voluptuous as vol

from .const import DOMAIN


class KanboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kanboard."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title="Kanboard",
                data={
                    CONF_URL: user_input[CONF_URL],
                    CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_URL): str,
                vol.Required(CONF_API_TOKEN): str,
            }),
            errors=errors,
        )
