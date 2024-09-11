from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_NAME, SCAN_INTERVAL
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL, CONF_TOKEN, CONF_MODEL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from miio import (
    Device as MiioDevice,
    DeviceException,
)
from homeassistant.helpers.device_registry import format_mac

import logging
_LOGGER = logging.getLogger(__name__)

async def check_miio_device(hass, user_input, errors):
    host = user_input.get(CONF_HOST)
    token = user_input.get(CONF_TOKEN)
    try:
        device = MiioDevice(host, token)
        info = await hass.async_add_executor_job(device.info)
    except DeviceException:
        device = None
        info = None
        errors['base'] = 'cannot_connect'
    _LOGGER.debug('Tokit cooker config flow: %s', {
        'user_input': user_input,
        'miio_info': info,
        'errors': errors,
    })
    model = ''
    if info is not None:
        if not user_input.get(CONF_MODEL):
            model = str(info.model or '')
            user_input[CONF_MODEL] = model
        user_input['miio_info'] = dict(info.raw or {})
        user_input['unique_did'] = format_mac(info.mac_address)
    return user_input

class TokitCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Tokit Cooker config flow."""
    VERSION = 1
    MINOR_VERSION = 1
    
    
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is None:
            user_input = {}
        else:
            await check_miio_device(self.hass, user_input, errors)
            if user_input.get('unique_did'):
                await self.async_set_unique_id(user_input['unique_did'])
                self._abort_if_unique_id_configured()
            return self.async_create_entry(
                    title=user_input.get(CONF_NAME),
                    data={k:v for k,v in user_input.items() if k in [CONF_HOST,CONF_TOKEN,CONF_MODEL]},
                    options={k:v for k,v in user_input.items() if k in [CONF_NAME,CONF_SCAN_INTERVAL]},
                )
                
        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, vol.UNDEFINED)): cv.string,
                vol.Required(CONF_TOKEN, default=user_input.get(CONF_TOKEN, vol.UNDEFINED)):
                    vol.All(cv.string, vol.Length(min=32, max=32)),
                vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=user_input.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL.total_seconds())):
                    cv.positive_int,
            }),
            errors=errors,
        )
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TokitOptionsFlow(config_entry)
    

class TokitOptionsFlow(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input = None):
        errors = {}
        if user_input is None:
            user_input = {}
        else:
            return self.async_create_entry(
                    title="",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=self.config_entry.options.get(CONF_NAME)): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL)):
                    cv.positive_int,
            }), errors=errors
        )