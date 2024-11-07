import logging
import requests
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "kanboardizer"

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

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Kanboardizer component."""
    conf = config[DOMAIN]
    hass.data[DOMAIN] = conf
    
    discovery.load_platform(hass, "sensor", DOMAIN, {}, config)
    discovery.load_platform(hass, "calendar", DOMAIN, {}, config)
    
    return True
