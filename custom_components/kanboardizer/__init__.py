"""The Kanboardizer component."""

import requests
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "Kanboardizer"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("api_url"): str,
                vol.Required("api_token"): str,
                vol.Required("user"): str,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass: HomeAssistant, config: dict):
    """Set up the Kanboardizer component."""
    hass.data[DOMAIN] = config[DOMAIN]
    return True
