
CUBE = 'Cube'
HEATING_THERMOSTAT = 'HeatingThermostat'
HEATING_THERMOSTAT_PLUS = 'HeatingThermostatPlus'
WALL_MOUNTED_THERMOSTAT = 'WallMountedThermostat'
SHUTTER_CONTACT = 'ShutterContact'
PUSH_BUTTON = 'PushButton'

# local constants
DEVICE_TYPES = {
    0: CUBE,
    1: HEATING_THERMOSTAT,
    2: HEATING_THERMOSTAT_PLUS,
    3: WALL_MOUNTED_THERMOSTAT,
    4: SHUTTER_CONTACT,
    5: PUSH_BUTTON
}
DEVICE_TYPES_BY_NAME = dict((v, k) for k, v in DEVICE_TYPES.items())

MODE_AUTO = 'auto'
MODE_MANUAL = 'manual'
MODE_TEMPORARY = 'temporary'
MODE_BOOST = 'boost'

MODE_IDS = {
    0: MODE_AUTO,
    1: MODE_MANUAL,
    2: MODE_TEMPORARY,
    3: MODE_BOOST,
}

SHUTTER_OPEN = 'open'
SHUTTER_CLOSED = 'closed'

SHUTTER_STATES = {
    0: SHUTTER_CLOSED,
    2: SHUTTER_OPEN,
}

DECALC_DAYS = {
    "Sat": 0,
    "Sun": 1,
    "Mon": 2,
    "Tue": 3,
    "Wed": 4,
    "Thu": 5,
    "Fri": 6
}

BOOST_DURATION = {
    0: 0,
    5: 1,
    10: 2,
    15: 3,
    20: 4,
    25: 5,
    30: 6,
    60: 7
}

MIN_TEMPERATURE = 4.5
MAX_TEMPERATURE = 30.5

EVENT_THERMOSTAT_UPDATE = 'thermostat_update'
EVENT_SHUTTER_UPDATE = 'shutter_update'
EVENT_PUSH_BUTTON_UPDATE = 'push_button_update'
EVENT_DEVICE_PAIRED = 'device_paired'
EVENT_DEVICE_REPAIRED = 'device_repaired'

ATTR_DEVICE_ID = 'device_id'
ATTR_DESIRED_TEMPERATURE = 'desired_temperature'
ATTR_MEASURED_TEMPERATURE = 'measured_temperature'
ATTR_MODE = 'mode'
ATTR_BATTERY_LOW = 'battery_low'
ATTR_DEVICE_TYPE = 'device_type'
ATTR_DEVICE_SERIAL = 'device_serial'
ATTR_FIRMWARE_VERSION = 'firmware_version'
ATTR_STATE = 'state'
