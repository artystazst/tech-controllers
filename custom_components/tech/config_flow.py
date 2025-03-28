"""Config flow for Tech Sterowniki integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.helpers import aiohttp_client
from .const import DOMAIN, SUPPORTED_LANGUAGES, CONF_LANGUAGE, DEFAULT_LANGUAGE
from .tech import Tech

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(SUPPORTED_LANGUAGES.keys()),
})


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    http_session = aiohttp_client.async_get_clientsession(hass)
    api = Tech(http_session)

    if not await api.authenticate(data["username"], data["password"]):
        raise InvalidAuth
    modules = await api.list_modules()

    language_code = SUPPORTED_LANGUAGES[data[CONF_LANGUAGE]]
    # Return info that you want to store in the config entry.
    return {
        "user_id": api.user_id,
        "token": api.token,
        "controllers": modules,
        CONF_LANGUAGE: language_code,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tech Sterowniki."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                controllers_names = ""
                for controller in info["controllers"]:
                    controllers_names += controller["version"] + " "

                return self.async_create_entry(title=controllers_names, data=info)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
