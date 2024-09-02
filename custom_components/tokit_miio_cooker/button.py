from datetime import time
from homeassistant.components.button import ButtonEntity, ENTITY_ID_FORMAT
from homeassistant.components.select import ENTITY_ID_FORMAT as SELECT_ENTITY_ID_FORMAT
from homeassistant.components.time import ENTITY_ID_FORMAT as TIME_ENTITY_ID_FORMAT
from homeassistant.components.switch import ENTITY_ID_FORMAT as SWITCH_ENTITY_ID_FORMAT
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from .utils import get_device_info, get_entity_id, get_unique_id
from .const import AUTO_KEEP_WARM, DOMAIN, DURATION, MENU, MENU_OPTIONS, SCHEDULE_TIME, SET_MENU, DEL_MENU
from miio.deviceinfo import DeviceInfo
from homeassistant.config_entries import ConfigEntry 
from miio.integrations.chunmi.cooker_tokit import TokitCooker
from . import TokitCookerCoordinator


import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    
    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    cooker: TokitCooker = hass.data[DOMAIN][config_entry.entry_id]["cooker"]
    coordinator: TokitCookerCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    def set_menu_index():
        entities = hass.data[DOMAIN][config_entry.entry_id]["entities"]
        menu_entity_id = get_entity_id(device_info, MENU, SELECT_ENTITY_ID_FORMAT)
        menu = entities[menu_entity_id].current_option
        if not menu:
            return 
        
        entities = hass.data[DOMAIN][config_entry.entry_id]["entities"]
        menu_options_entity_id = get_entity_id(device_info, MENU_OPTIONS, SELECT_ENTITY_ID_FORMAT)
        menu_option = entities[menu_options_entity_id].current_option
        
        duration_entity_id = get_entity_id(device_info, DURATION, TIME_ENTITY_ID_FORMAT)
        duration_time: time = entities[duration_entity_id].native_value
        duration = duration_time.hour*60 + duration_time.minute
        
        auto_keep_warm_entity_id = get_entity_id(device_info, AUTO_KEEP_WARM, SWITCH_ENTITY_ID_FORMAT)
        auto_keep_warm: bool = entities[auto_keep_warm_entity_id].is_on
        
        schedule_entity_id = get_entity_id(device_info, SCHEDULE_TIME, TIME_ENTITY_ID_FORMAT)
        schedule_time: time = entities[schedule_entity_id].native_value
        schedule = schedule_time.hour*60 + schedule_time.minute
        
        cooker.set_menu(name = menu, index=int(menu_option[0]), duration=duration, schedule=schedule, auto_keep_warm=auto_keep_warm)
    
    def del_menu_index():
        entities = hass.data[DOMAIN][config_entry.entry_id]["entities"]
        menu_options_entity_id = get_entity_id(device_info, MENU_OPTIONS, SELECT_ENTITY_ID_FORMAT)
        menu_option = entities[menu_options_entity_id].current_option
        cooker.delete_menu(int(menu_option[0]))
    
    configs = [
        ("mdi:menu", SET_MENU, set_menu_index),
        ("mdi:menu", DEL_MENU, del_menu_index)
    ]
    entities = []
    for config in configs:
        entity = MenuButton(coordinator, device_info, device_name, config)
        entities.append(entity)
    
    async_add_entities(entities)

class MenuButton(ButtonEntity):
    
    def __init__(self, coordinator, device_info, device_name, config):
        """Initialize switch entity."""
        self.coordinator: TokitCookerCoordinator = coordinator
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        
        self._attr_icon = config[0]
        self._attr = config[1]
        self._button_func = config[2]
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr
    
    async def async_press(self) -> None:
        """Handle the button press."""
        self._button_func()
        await self.coordinator.async_request_refresh()
        
        
