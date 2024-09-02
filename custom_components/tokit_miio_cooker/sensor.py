from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass, ENTITY_ID_FORMAT, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_NAME

from custom_components.tokit_miio_cooker.utils import get_device_info, get_entity_id, get_unique_id
from .const import DOMAIN, DURATION, MENU, MENU_OPTIONS, SCHEDULE_TIME, START_TIME, FINISH_TIME, REMAINING, STATUS, TEMPERATURE
from miio.integrations.chunmi.cooker_tokit.cooker_tokit import STATUS_MAPPING, COOK_MODE_NAME_MAPPING
from miio.deviceinfo import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import logging
_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = [
    (SensorDeviceClass.ENUM, None, STATUS, None, "mdi:eye", None),
    (SensorDeviceClass.ENUM, None, MENU, None, "mdi:menu", None),
    (SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, TEMPERATURE, "°C", "mdi:temperature-celsius", None),
    (SensorDeviceClass.DURATION, None, REMAINING, "s", "mdi:timer", lambda t: int(t.total_seconds())),
    (SensorDeviceClass.DURATION, None, DURATION, "min", "mdi:timelapse", lambda t: int(t.total_seconds()//60)),
    (None, None, SCHEDULE_TIME, None, "mdi:clock", None),
    (SensorDeviceClass.TIMESTAMP, None, START_TIME, None, "mdi:clock", None),
    (SensorDeviceClass.TIMESTAMP, None, FINISH_TIME, None, "mdi:clock", None),
    # (None, None, MENU_OPTIONS, None, "mdi:format-list-numbered", lambda l: ",".join(l))
]

SENSOR_ENUM_OPTIONS = {
    "status": list(STATUS_MAPPING.values()),
    "menu" :list(COOK_MODE_NAME_MAPPING.keys())
}
    

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up entry."""
    sensors = []
    
    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    for sensor_type_config in SENSOR_TYPES:
        tokit_cooker_sensor = TokitCookerSensor(coordinator, device_info, device_name, sensor_type_config)
        sensors.append(tokit_cooker_sensor)
    
    async_add_entities(sensors)
    device_entry = sensors[0].device_entry
    if device_entry:
        if "devices" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["devices"][device_entry.id] = device_entry
        else:
            hass.data[DOMAIN]["devices"] = {device_entry.id: device_entry}
    
    
class TokitCookerSensor(CoordinatorEntity, SensorEntity):
    
    def __init__(self, coordinator, device_info, device_name, sensor_config):
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        self._attr_device_class = sensor_config[0]
        self._attr_state_class = sensor_config[1]
        self._attr = sensor_config[2]
        self._unit_of_measurement = sensor_config[3]
        self._attr_icon = sensor_config[4]
        self._state = None
        self._state_func = sensor_config[5]
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
    def state(self):
        """Return the state."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement the state is expressed in."""
        return self._unit_of_measurement
        
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        state = getattr(self.coordinator.data, self._attr, None)
        if self._state_func:
            self._state = self._state_func(state)
        else:
            self._state = state
        self.async_write_ha_state()