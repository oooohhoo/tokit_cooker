from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from .utils import get_device_info, get_entity_id, get_unique_id
from .const import AUTO_KEEP_WARM, DOMAIN
from homeassistant.core import callback
from miio.deviceinfo import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    
    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    auto_keep_warm_sensor = AutoKeepWarmSensor(coordinator, device_info, device_name)

    async_add_entities([auto_keep_warm_sensor])
    
class AutoKeepWarmSensor(CoordinatorEntity, BinarySensorEntity):
    
    def __init__(self, coordinator, device_info, device_name):
        """Initialize binary sensor entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        self._attr_icon = "mdi:fire"
        self._attr = AUTO_KEEP_WARM
        self._attr_is_on = None
        
        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        
    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)
        
    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = getattr(self.coordinator.data, self._attr)
        self.async_write_ha_state()