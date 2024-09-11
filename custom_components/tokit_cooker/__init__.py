from datetime import timedelta
from typing import Any, Optional
from homeassistant import core
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL, CONF_TOKEN, CONF_MODEL, CONF_NAME
from .const import COOKER_DEL_MENU, COOKER_SET_MENU, COOKER_START, COOKER_STOP, DOMAIN, SUPPORTED_MODELS
from homeassistant.helpers import device_registry, storage
from homeassistant import config_entries
from miio import TokitCooker, DeviceException
from homeassistant.exceptions import PlatformNotReady, ServiceValidationError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.debounce import Debouncer
import async_timeout


import logging
_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.TIME, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.BUTTON]

def bind_services_to_device(hass: core.HomeAssistant):
    def get_cooker(call) -> TokitCooker:
        device_ids = call.data.get('device_id')
        if not device_ids or len(device_ids) > 1:
            raise ServiceValidationError("More than 1 device selected.")
        device_id = device_ids[0]
        device = hass.data[DOMAIN].get("devices",{}).get(device_id)
        if not device:
            _LOGGER.warning('Call service failed: Device not found for %s', device_id)
            return
        config_entry_id = list(device.config_entries)[0]
        return hass.data[DOMAIN][config_entry_id]["cooker"]
        
    async def cooker_stop(call):
        """Service to stop cooking."""
        _LOGGER.debug(f"service data: {call.data}")
        device_ids = call.data.get('device_id')
        if not device_ids:
            raise ServiceValidationError("No tokit devices selected.")

        cookers = []
        dentry: device_registry.DeviceEntry
        for did, dentry in hass.data[DOMAIN].get("devices",{}).items():
            if did in device_ids:
                config_entry_id = list(dentry.config_entries)[0]
                cookers.append(hass.data[DOMAIN][config_entry_id]["cooker"])
        
        if not cookers:
            _LOGGER.warning('Call service failed: Device(s) not found for %s', device_ids)
            return
        for cooker in cookers:
            cooker.stop() 
            
    async def cooker_start(call):
        """Service to start cooking."""
        _LOGGER.warning(call.data)
        cooker = get_cooker(call)
        cooker.start(
            call.data.get("name"),
            call.data.get("duration"),
            call.data.get("schedule"),
            call.data.get("auto_keep_warm"),
        )
        
    async def cooker_del_menu(call):
        """Service to delete menu."""
        cooker = get_cooker(call)
        cooker.delete_menu(call.data["index"])
        
    async def cooker_set_menu(call):
        """Service to set menu."""
        cooker = get_cooker(call)
        cooker.set_menu(call.data["name"],
                        call.data["index"],
                        call.data.get("duration"),
                        call.data.get("schedule"),
                        call.data.get("auto_keep_warm"))

    hass.services.async_register(DOMAIN, COOKER_STOP, cooker_stop)
    hass.services.async_register(DOMAIN, COOKER_START, cooker_start)
    hass.services.async_register(DOMAIN, COOKER_DEL_MENU, cooker_del_menu)
    hass.services.async_register(DOMAIN, COOKER_SET_MENU, cooker_set_menu)
    

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    
    if "config_entries" in hass.data[DOMAIN]:
        hass.data[DOMAIN]["config_entries"][config_entry.entry_id] = config_entry
    else:
        hass.data[DOMAIN]["config_entries"] = {config_entry.entry_id: config_entry}
        
    host = config_entry.data[CONF_HOST]
    token = config_entry.data[CONF_TOKEN]
    model = config_entry.data.get(CONF_MODEL)
    name = config_entry.options[CONF_NAME]
    scan_interval = config_entry.options[CONF_SCAN_INTERVAL]
        
    try:
        cooker = TokitCooker(host, token)
        device_info = cooker.info()
        if model is None:
            model = device_info.model
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
    except DeviceException:
        raise PlatformNotReady
    
    if model not in SUPPORTED_MODELS:
        _LOGGER.error(
            f"Unsupported device found: {model}"
        )
        return False

    if not config_entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN][config_entry.entry_id] = {
            "device_info": device_info,
            "cooker": cooker,
            "entities": {}
        }
    if isinstance(scan_interval, int):
        scan_interval = timedelta(seconds=scan_interval)
    
    if "coordinator" in hass.data[DOMAIN][config_entry.entry_id]:
        tokit_cooker_coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        tokit_cooker_coordinator.update_interval=scan_interval
    else:
        tokit_cooker_coordinator = TokitCookerCoordinator(hass, cooker, scan_interval)
        hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = tokit_cooker_coordinator

    bind_services_to_device(hass)
      
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    await tokit_cooker_coordinator.async_config_entry_first_refresh()
    
    config_entry.async_on_unload(config_entry.add_update_listener(options_update_listener))
    
    return True

async def options_update_listener(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Handle options update."""
    # _LOGGER.warning("options_update_listener")
    await hass.config_entries.async_reload(entry.entry_id)
    
    
async def async_unload_entry(hass: core.HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class TokitCookerCoordinator(DataUpdateCoordinator):
    """Tokit Cooker coordinator."""

    def __init__(self, hass, cooker, scan_interval):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Tokit Cooker sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=scan_interval,
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=1,  # update immediately when turn off or turn on
                immediate=True
            )
        )
        self.cooker: TokitCooker = cooker
        
    async def _async_update_data(self):
        """Fetch data.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        async with async_timeout.timeout(10):
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
            try:
                return self.cooker.status()
            except Exception as err:
                raise UpdateFailed(f"Error communicating with the cooker: {err}")