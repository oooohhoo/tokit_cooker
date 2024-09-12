from datetime import timedelta
from miio.integrations.chunmi.cooker_tokit.cooker_tokit import MODEL_TK4001

DOMAIN = "tokit_cooker"
DEFAULT_NAME = "TOKIT Miio Cooker"
SCAN_INTERVAL = timedelta(seconds=30)

SUPPORTED_MODELS = [MODEL_TK4001]

# Services
COOKER_STOP = "cooker_stop"
COOKER_START = "cooker_start"
COOKER_SET_MENU = "cooker_set_menu"
COOKER_DEL_MENU = "cooker_del_menu"

# Entity attributes
DURATION = "duration"
SCHEDULE_TIME = "schedule_time"
AUTO_KEEP_WARM = "auto_keep_warm"
MENU = "menu"
MENU_OPTIONS = "menu_options"
STATUS = "status"
REMAINING = "remaining"
START_TIME = "start_time"
FINISH_TIME = "finish_time"
COOKER = "cooker"
TEMPERATURE = "temperature"
RESERVATION = "reservation"
RUNNING = "running"
SET_MENU = "set_menu"
DEL_MENU = "del_menu"
