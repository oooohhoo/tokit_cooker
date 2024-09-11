from homeassistant.components.select import SelectEntity
from homeassistant.components.select import ENTITY_ID_FORMAT
from homeassistant.components.time import ENTITY_ID_FORMAT as TIME_ENTITY_ID_FORMAT
from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from datetime import time
from homeassistant.core import callback

from .utils import get_device_info, get_entity_id, get_unique_id
from .const import DOMAIN, DURATION, MENU, MENU_OPTIONS
from miio.integrations.chunmi.cooker_tokit.cooker_tokit import CookerProfile, COOK_MODE_NAME_MAPPING, COOK_MODE_DETAIL_MAPPING
from miio.deviceinfo import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from . import TokitCookerCoordinator
from homeassistant.helpers.update_coordinator import CoordinatorEntity


import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    
    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    coordinator: TokitCookerCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    async def menu_changed(menu):
        cook_mode_id = COOK_MODE_NAME_MAPPING[menu]
        profile_hex = COOK_MODE_DETAIL_MAPPING[cook_mode_id]["cookScript"]
        cooker_profile = CookerProfile(profile_hex=profile_hex)
        duration = cooker_profile.get_duration()
        entity_id = get_entity_id(device_info, DURATION, TIME_ENTITY_ID_FORMAT)
        duration_entity: TimeEntity = hass.data[DOMAIN][config_entry.entry_id]["entities"][entity_id]
        await duration_entity.async_set_value(time(hour=duration//60, minute=duration % 60))
    
    configs = (
        ("mdi:menu", MENU, menu_changed),
        ("mdi:format-list-numbered", MENU_OPTIONS, None) 
    )
    
    menu_select_entity = MenuSelect(device_info, device_name, menu_changed)
    menu_options_select_entity = MenuOptionsSelect(coordinator, device_info, device_name)
    hass.data[DOMAIN][config_entry.entry_id]["entities"][menu_select_entity.entity_id] = menu_select_entity
    hass.data[DOMAIN][config_entry.entry_id]["entities"][menu_options_select_entity.entity_id] = menu_options_select_entity

    async_add_entities([menu_select_entity, menu_options_select_entity])
    
class MenuOptionsSelect(CoordinatorEntity, SelectEntity):
    # Available menus on cooker dashboard
    def __init__(self, coordinator, device_info, device_name):
        """Initialize select entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        self._attr = MENU_OPTIONS
        self._attr_icon = "mdi:format-list-numbered"
        self._attr_current_option = None
        self._attr_options = list()
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr
        
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        menu_options: list = getattr(self.coordinator.data, self._attr, None)
        self._attr_options = [f"{i+1}({menu})" for i,menu in enumerate(menu_options)]
        menu = getattr(self.coordinator.data, MENU, None)
        if menu and menu in menu_options:
            self._attr_current_option = f"{menu_options.index(menu)+1}({menu})"
        else:
            self._attr_current_option = self._attr_options[-1]
        self.async_write_ha_state()
    

class MenuSelect(SelectEntity):
    # All available menus
    def __init__(self, device_info, device_name, select_option_func):
        """Initialize select entity."""
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        self._attr = MENU
        self._attr_icon = "mdi:menu"
        self._select_option_func = select_option_func
        self._attr_current_option = None
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr

    @property
    def options(self) -> list:
        return list(COOK_MODE_NAME_MAPPING)
        
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._select_option_func(option)
        self._attr_current_option = option