import slugify

from .const import DOMAIN

def get_device_info(device_name, device_info):
    return {
        'identifiers': {(DOMAIN, f"{device_info.model.replace(".","_").lower()}_{device_info.mac_address.replace(":","_").lower()}")},
        'name': device_name,
        'model': device_info.model,
        'manufacturer': 'TOKIT',
        'sw_version': device_info.firmware_version,
        'hw_version': device_info.hardware_version
    }

def get_entity_id(device_info, attr, ENTITY_ID_FORMAT: str ):
    return ENTITY_ID_FORMAT.format(f"{device_info.model.replace(".","_").lower()}_{attr}")

def get_unique_id(device_info, attr, ENTITY_ID_FORMAT: str):
    return ENTITY_ID_FORMAT.format(f"{device_info.model.replace(".","_").lower()}_{attr}_{device_info.mac_address.replace(":","_").lower()}")