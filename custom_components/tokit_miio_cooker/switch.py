from datetime import time
from functools import partial
from typing import Any
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.components.switch import ENTITY_ID_FORMAT
from homeassistant.components.select import ENTITY_ID_FORMAT as SELECT_ENTITY_ID_FORMAT
from homeassistant.components.time import ENTITY_ID_FORMAT as TIME_ENTITY_ID_FORMAT
from homeassistant.components.switch import ENTITY_ID_FORMAT as SWITCH_ENTITY_ID_FORMAT
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback
from . import TokitCookerCoordinator
from .utils import get_device_info, get_entity_id, get_unique_id
from .const import AUTO_KEEP_WARM, DOMAIN, DURATION, MENU, RESERVATION, RUNNING, SCHEDULE_TIME, STATUS
from miio.deviceinfo import DeviceInfo
from miio.integrations.chunmi.cooker_tokit import TokitCooker
from homeassistant.config_entries import ConfigEntry 

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    
    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    cooker: TokitCooker = hass.data[DOMAIN][config_entry.entry_id]["cooker"]
    coordinator: TokitCookerCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        
    def cooker_start(switch):
        entities = hass.data[DOMAIN][config_entry.entry_id]["entities"]
        menu_entity_id = get_entity_id(device_info, MENU, SELECT_ENTITY_ID_FORMAT)
        menu = entities[menu_entity_id].current_option
        if not menu:
            return 
        duration_entity_id = get_entity_id(device_info, DURATION, TIME_ENTITY_ID_FORMAT)
        duration_time: time = entities[duration_entity_id].native_value
        duration = duration_time.hour*60 + duration_time.minute
        
        auto_keep_warm_entity_id = get_entity_id(device_info, AUTO_KEEP_WARM, SWITCH_ENTITY_ID_FORMAT)
        auto_keep_warm: bool = entities[auto_keep_warm_entity_id].is_on
        if switch._attr == RUNNING:
            cooker.start(name = menu, duration=duration,auto_keep_warm=auto_keep_warm)
        else:
            schedule_entity_id = get_entity_id(device_info, SCHEDULE_TIME, TIME_ENTITY_ID_FORMAT)
            schedule_time: time = entities[schedule_entity_id].native_value
            schedule = schedule_time.hour*60 + schedule_time.minute
            cooker.start(name = menu, duration=duration, schedule=schedule, auto_keep_warm=auto_keep_warm)
    
    def cooker_stop(switch):
        cooker.stop()
    
    configs = [
        ("mdi:play", RUNNING, cooker_start, cooker_stop),
        ("mdi:clock-outline", RESERVATION, cooker_start, cooker_stop)
    ]
    
    entities = []
    for config in configs:
        entities.append(TokitCookerSwitch(coordinator, device_info, device_name, config))
        
    entity = AutoKeepWarmSwitch(device_info, device_name)
    hass.data[DOMAIN][config_entry.entry_id]["entities"][entity.entity_id] = entity
    entities.append(entity)
    
    async_add_entities(entities)
    
class TokitCookerSwitch(CoordinatorEntity, SwitchEntity):
    
    def __init__(self, coordinator, device_info, device_name, config):
        """Initialize switch entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        
        self._attr_icon = config[0]
        self._attr = config[1]
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_is_on = None
        self._turn_on_func = partial(config[2], self)
        self._turn_off_func = partial(config[3], self)
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr
        
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._turn_off_func()
        self._attr_is_on = False
        await self.coordinator.async_request_refresh()
        
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._turn_on_func()
        self._attr_is_on = True
        await self.coordinator.async_request_refresh()
         
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        status = getattr(self.coordinator.data, STATUS, None)
        cooker_running = status != "IDLE" and status != "RESERVATION"
        reservation = status == "RESERVATION"
        if self._attr == RUNNING:
            self._attr_is_on = cooker_running
        else:
            self._attr_is_on = reservation
        self.async_write_ha_state()
        
class AutoKeepWarmSwitch(SwitchEntity):
    
    def __init__(self, device_info, device_name):
        """Initialize switch entity."""
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        
        self._attr_icon = "mdi:fire"
        self._attr = AUTO_KEEP_WARM
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_is_on = True
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr
    
    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        
    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._attr_is_on = True