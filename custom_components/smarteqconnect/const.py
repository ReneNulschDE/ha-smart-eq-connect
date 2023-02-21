"""Constants for the Smart EQ connect 2021 integration."""
import logging
from enum import Enum

import voluptuous as vol
from homeassistant.const import LENGTH_KILOMETERS, PERCENTAGE
from homeassistant.helpers import config_validation as cv

SMARTEQ_COMPONENTS = [
    "sensor",
    #    "lock",
    "binary_sensor",
    #    "device_tracker",
    #    "switch"
]

REGION_EUROPE = "Europe"
REGION_NORAM = "North America"
REGION_APAC = "Asia-Pacific"

CONF_ALLOWED_REGIONS = [REGION_EUROPE]
CONF_LOCALE = "locale"
CONF_COUNTRY_CODE = "country_code"
CONF_EXCLUDED_CARS = "excluded_cars"
CONF_PIN = "pin"
CONF_REGION = "region"
CONF_VIN = "vin"
CONF_TIME = "time"
CONF_DEBUG_FILE_SAVE = "save_files"

DATA_CLIENT = "data_client"

DOMAIN = "smarteqconnect"
LOGGER = logging.getLogger(__package__)

DEFAULT_CACHE_PATH = "custom_components/smarteqconnect/messages"
DEFAULT_TOKEN_PATH = ".smarteqconnect-token-cache"
DEFAULT_LOCALE = "en-GB"
DEFAULT_COUNTRY_CODE = "EN"

DEVICE_USER_AGENT = "Device: iPhone13,3; OS-version: iOS_15.0.2; App-Name: smart EQ control; App-Version: 3.0; Build: 202108260942; Language: de_DE"

SYSTEM_PROXY = None
PROXIES = {}

# SYSTEM_PROXY = "http://localhost:8080"
# PROXIES = {
#  'https': SYSTEM_PROXY,
# }
VERIFY_SSL = False

ATTR_MB_MANUFACTURER = "Mercedes Benz"
LOGIN_APP_ID_EU = "70d89501-938c-4bec-82d0-6abb550b0825"
LOGIN_BASE_URI = "https://id.mercedes-benz.com"
LOGIN_BASE_URI_NA = "https://id.mercedes-benz.com"
LOGIN_BASE_URI_PA = "https://id.mercedes-benz.com"
REST_API_BASE = "https://oneapp.microservice.smart.com"


SERVICE_REFRESH_TOKEN_URL = "refresh_access_token"
SERVICE_PREHEAT_START = "preheat_start"
SERVICE_PREHEAT_START_DEPARTURE_TIME = "preheat_start_departure_time"
SERVICE_PREHEAT_STOP = "preheat_stop"
SERVICE_VIN_SCHEMA = vol.Schema({vol.Required(CONF_VIN): cv.string})
SERVICE_VIN_TIME_SCHEMA = vol.Schema(
    {vol.Required(CONF_VIN): cv.string, vol.Required(CONF_TIME): vol.All(vol.Coerce(int), vol.Range(min=0, max=1439))}
)
SERVICE_PREHEAT_START_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VIN): cv.string,
        vol.Required("type", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
    }
)

# "internal_name":[ 0 Display_Name
#                   1 unit_of_measurement,
#                   2 object in car.py
#                   3 attribute in car.py
#                   4 value field
#                   5 unused --> None (for capabilities check in the future)
#                   6 [list of extended attributes]
#                   7 icon
#                   8 device_class
#                   9 invert boolean value - Default: False
# ]

BINARY_SENSORS = {
    "tirewarningsrdk": [
        "Tire Warning",
        None,
        "tires",
        "tirewarningsrdk",
        "value",
        None,
        {},
        "mdi:car-tire-alert",
        "problem",
        False,
    ],
    "chargingactive": [
        "Charging active",
        None,
        "electric",
        "chargingactive",
        "value",
        None,
        {},
        None,
        "battery_charging",
        False,
    ],
    "precondactive": ["Precond active", None, "electric", "precondNow", "value", None, {}, None, "radiator", False],
}

DEVICE_TRACKER = {}

SENSORS = {
    "rangeElectricKm": [
        "Range Electric",
        LENGTH_KILOMETERS,
        "electric",
        "rangeelectric",
        "value",
        None,
        {"electricconsumptionstart", "soc", "chargingactive", "chargingstatus"},
        "mdi:ev-station",
        None,
        False,
    ],
    "soc": ["State of Charge", PERCENTAGE, "electric", "soc", "value", None, {}, "mdi:ev-station", None, False],
    "odometer": [
        "Odometer",
        LENGTH_KILOMETERS,
        "odometer",
        "odo",
        "value",
        None,
        {
            "ecoScoreFluentDriving",
            "ecoScoreSpeed",
            "ecoscoretotal",
            "serviceintervaldistance",
        },
        "mdi:car-cruise-control",
        None,
        False,
    ],
}

LOCKS = {}

SWITCHES = {}


class Sensor_Config_Fields(Enum):
    # "internal_name":[ 0 Display_Name
    #                   1 unit_of_measurement,
    #                   2 object in car.py
    #                   3 attribute in car.py
    #                   4 value field
    #                   5 unused --> None (for capabilities check in the future)
    #                   6 [list of extended attributes]
    #                   7 icon
    #                   8 device_class
    #                   9 invert boolean value - Default: False
    # ]
    DISPLAY_NAME = 0
    UNIT_OF_MEASUREMENT = 1
    OBJECT_NAME = 2
    ATTRIBUTE_NAME = 3
    VALUE_FIELD_NAME = 4
    CAPABILITIES_LIST = 5
    EXTENDED_ATTRIBUTE_LIST = 6
    ICON = 7
    DEVICE_CLASS = 8
    FLIP_RESULT = 9
