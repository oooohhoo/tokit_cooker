from datetime import time
from homeassistant.components.time import TimeEntity
from homeassistant.components.time import ENTITY_ID_FORMAT
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from .utils import get_device_info, get_entity_id, get_unique_id
from .const import DOMAIN, DURATION, SCHEDULE_TIME
from miio.deviceinfo import DeviceInfo
from homeassistant.config_entries import ConfigEntry

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up entry."""

    device_name = config_entry.options[CONF_NAME]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]

    configs = [
        ["mdi:alarm-check", SCHEDULE_TIME, time(hour=17)],
        ["mdi:progress-clock", DURATION, None],
    ]

    entities = []
    for config in configs:
        entity = TokitCookerTime(device_info, device_name, config)
        hass.data[DOMAIN][config_entry.entry_id]["entities"][entity.entity_id] = entity
        entities.append(entity)

    async_add_entities(entities)


class TokitCookerTime(TimeEntity):
    def __init__(self, device_info, device_name, config):
        """Initialize time entity."""
        self._attr_has_entity_name = True
        self._device_info: DeviceInfo = device_info
        self._device_name = device_name
        self._attr_icon = config[0]
        self._attr = config[1]
        self._attr_native_value = config[2]

        self.entity_id = get_entity_id(self._device_info, self._attr, ENTITY_ID_FORMAT)
        self._attr_unique_id = get_unique_id(
            self._device_info, self._attr, ENTITY_ID_FORMAT
        )

    @property
    def device_info(self):
        return get_device_info(self._device_name, self._device_info)

    @property
    def translation_key(self):
        """Return the translation key."""
        return self._attr

    async def async_set_value(self, value: time) -> None:
        """Change the time."""
        self._attr_native_value = value
        self.async_write_ha_state()
