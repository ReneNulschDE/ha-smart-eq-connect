"""Config flow for HVV integration."""
import logging
import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import CONF_PASSWORD, CONF_SOURCE, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client

from .client import Client
from .const import (  # pylint:disable=unused-import
    CONF_ALLOWED_REGIONS,
    CONF_COUNTRY_CODE,
    CONF_DEBUG_FILE_SAVE,
    CONF_EXCLUDED_CARS,
    CONF_LOCALE,
    CONF_REGION,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_LOCALE,
    DOMAIN,
    VERIFY_SSL,
)
from .errors import MbapiError

_LOGGER = logging.getLogger(__name__)

SCHEMA_STEP_USER = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_REGION): vol.In(CONF_ALLOWED_REGIONS)}
)

SCHEMA_STEP_PIN = vol.Schema({vol.Required(CONF_PASSWORD): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for smarteq."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize component."""
        self._existing_entry = None
        self.data = None
        self.reauth_mode = False
        self.session = None
        self.client = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:

            await self.async_set_unique_id(DOMAIN)

            if not self.reauth_mode:
                self._abort_if_unique_id_configured()

            self.session = aiohttp_client.async_get_clientsession(self.hass, VERIFY_SSL)

            self.client = Client(session=self.session, hass=self.hass, region=user_input[CONF_REGION])
            try:
                result = await self.client.oauth.request_pin(user_input[CONF_USERNAME])
            except MbapiError as error:
                errors = error

            if not errors:
                self.data = user_input
                return await self.async_step_pin()
            else:
                _LOGGER.error("Request Pin Error: %s", errors)

        return self.async_show_form(step_id="user", data_schema=SCHEMA_STEP_USER, errors="Error unknow")  # errors

    async def async_step_pin(self, user_input=None):
        """Handle the step where the user inputs his/her station."""

        errors = {}

        if user_input is not None:

            pin = user_input[CONF_PASSWORD]

            try:
                result = await self.client.oauth.request_access_token(self.data[CONF_USERNAME], pin)
            except MbapiError as error:
                _LOGGER.error("Request Token Error: %s", errors)
                errors = error
            except TypeError as terror:
                errors = None
                result = "{}"

            if not errors:
                _LOGGER.debug("token received")
                self.data["token"] = result

                if self.reauth_mode:
                    self.hass.async_create_task(self.hass.config_entries.async_reload(self._existing_entry.entry_id))
                    return self.async_abort(reason="reauth_successful")

                return self.async_create_entry(title=DOMAIN, data=self.data)

        return self.async_show_form(step_id="pin", data_schema=SCHEMA_STEP_PIN, errors=errors)

    async def async_step_reauth(self, user_input=None):
        """Get new tokens for a config entry that can't authenticate."""

        self.reauth_mode = True
        self._existing_entry = user_input

        return self.async_show_form(step_id="user", data_schema=SCHEMA_STEP_USER, errors="Error unknow")  # errors

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(title=DOMAIN, data=self.options)

        options = self.config_entry.options
        country_code = options.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE)
        locale = options.get(CONF_LOCALE, DEFAULT_LOCALE)
        excluded_cars = options.get(CONF_EXCLUDED_CARS, "")
        save_debug_files = options.get(CONF_DEBUG_FILE_SAVE, False)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_COUNTRY_CODE, default=country_code): str,
                    vol.Optional(CONF_LOCALE, default=locale): str,
                    vol.Optional(CONF_EXCLUDED_CARS, default=excluded_cars): str,
                    vol.Optional(CONF_DEBUG_FILE_SAVE, default=save_debug_files): bool,
                }
            ),
        )
