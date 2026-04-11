from homeassistant.const import (
    UnitOfElectricPotential, UnitOfPressure, UnitOfSpeed,
    REVOLUTIONS_PER_MINUTE, UnitOfVolume, UnitOfVolumeFlowRate, PERCENTAGE
)

DOMAIN = 'zont_ws'
MANUFACTURER = 'MicroLine'
CONFIGURATION_URL = 'https://my.zont.online/'

ENTRIES = 'entries'
CURRENT_ENTITY_IDS = 'current_entity_ids'

LOGIN_DEFAULT = 'admin'
PASSWORD_DEFAULT = 'admin'
URL_DEFAULT = 'https://192.168.1.40/ws'

TIME_UPDATE = 60
WS_TIMEOUT_REQUEST = 5
HEARTBEAT = 60
TIMEOUT_RECONNECT = 10
COUNTER_REPEAT = 30
TIME_OUT_REPEAT = 9

DELTA_KELVINS = 2730

WS_KEY_USER = 'user'
WS_KEY_PASS = 'pass'
WS_KEY_AUTH = 'auth'
WS_AUTH_SUCCESS = 200
WS_AUTH_ERROR = 401
WS_KEY_REQUEST_IDS = 'req_ids'
WS_KEY_IDS = 'ids'
WS_KEY_ID = 'id'
WS_KEY_MODE_ID = 'm_id'
WS_KEY_MODE = 'm'
WS_KEY_CURRENT_TEMP = 'c'
WS_KEY_TARGET_TEMP = 's'
WS_KEY_STATE = 's'
WS_KEY_REQUEST_STATE = 'req_state'
WS_KEY_TYPE = 'type'
WS_KEY_NAME = 'name'
WS_KEY_STYPE = 'stype'
WS_KEY_CMD = 'cmd'
WS_KEY_CMD_RESPONSE = 'cmdres'
WS_KEY_SERVICE_CMD = 'scmd'
WS_KEY_SERVICE_CMD_RESPONSE = 'scmdres'
WS_KEY_TEMPERATURE = 't'
WS_KEY_AVAILABLE = 'a'
WS_KEY_FAILED = 'failed'
WS_KEY_TRIGGERED = 'trig'
WS_KEY_WATER_BOILER = 'water'
WS_KEY_DHW_BOILER = 'dhw'
WS_KEY_MODUL_BOILER = 'modul'
WS_KEY_PRESS_BOILER = 'press'
WS_KEY_STATE_BOILER = 'state'
WS_KEY_ERR_BOILER = 'err'
WS_KEY_FAILURE = 'f'
WS_KEY_UNIT = 'u'
WS_KEY_VALUE = 'v'
WS_KEY_HUMIDITY = 'h'
WS_KEY_BATTERY = 'b'
WS_KEY_RSSI = 'r'

COMMAND_ON = 1
COMMAND_OFF = 0


class ZontType:
    """Types of controls."""

    ANALOG_INPUT = 0
    DS18_TEMP_SENSOR = 1
    SECURITY_ZONE = 2
    CSH_ADAPTER = 6
    RADIO_SENSOR = 8
    WEB_ELEMENT = 10
    RELAY = 14
    MIXER = 15
    HEATING_CIRCUIT = 16
    PUMP = 17
    MODE = 20
    NTC_TEMP_SENSOR = 27
    ANY = 255


class ZontSysCommand:
    """System commands."""

    DATE = 'SDATE'
    RESTART = 'SRESTART'
    SERIAL_NUMBER = '#S54'
    DEVICE_INFO = '#S7'
    GSM_INFO = '#S4'
    NETWORK_INFO = '#S205'
    WIFI_INFO = '#S198'
    SERVER_INFO = '#S224'
    IMEI = '#S216'
    VOLTAGE = '#S6'
    TIME_ZONE = '#S36'


INIT_SYS_COMMANDS = [
    ZontSysCommand.DEVICE_INFO,
    ZontSysCommand.SERIAL_NUMBER,
    ZontSysCommand.GSM_INFO,
    ZontSysCommand.NETWORK_INFO,
    ZontSysCommand.WIFI_INFO,
    ZontSysCommand.SERVER_INFO,
    ZontSysCommand.IMEI,
    ZontSysCommand.VOLTAGE,
    ZontSysCommand.TIME_ZONE,
]


class RadioType:
    """Subtypes for radio sensor."""

    REMOTE_3_BUTTON = 2
    REMOTE_4_BUTTON = 3
    RADIO_RELAY_LOCK = 4
    RADIO_THERMOMETER = 5
    RADIO_DUCT = 6
    HOOD_MODULE = 7
    RADIO_TAG = 8
    LEAK_SENSOR = 10
    MOTION_SENSOR = 11
    SHOCK_SENSOR = 12
    MULTI_THERMOMETER = 13
    POWER_METER = 14
    EXTERNAL_TEMP_SENSOR = 15
    WATER_GAS_METER = 16
    RADIO_SOCKET_220V = 17
    TEMP_HUMIDITY_SENSOR = 18
    TAG_ACCELEROMETER = 19
    TAG_BATTERY = 20
    RADIO_PANEL = 23


ZONT_BINARY_SENSORS_RDIO = (RadioType.LEAK_SENSOR, RadioType.MOTION_SENSOR, )


class ZontWebElmType:
    """Types of web elements."""

    BINARY = 0
    BUTTON = 1
    SWITCH = 2
    ANALOG = 3


class ZontAnalogType:
    """Type of the analog input."""

    ANALOG = 0
    PRESSURE_5_BAR = 1
    PRESSURE_12_BAR = 2
    DOOR_SENSOR = 3
    MOTION_SENSOR_CONTROL = 4
    SMOKE_SENSOR = 5
    LEAK_SENSOR = 6
    MOTION_SENSOR = 7
    ROOM_THERMOSTAT = 8
    BOILER_ALARM_PLUS = 9
    BOILER_ALARM_MINUS = 10
    IGNITION_INPUT = 11
    SPEED_SENSOR = 12
    ENGINE_RPM_SENSOR = 13
    DIGITAL_INPUT = 14
    ALARM_BUTTON = 15
    FUEL_FLOW_SENSOR = 16
    HUMIDITY_SENSOR = 17
    PRESSURE_6_BAR = 18
    DIGITAL_INPUT_NO = 19
    DIGITAL_INPUT_NC = 20
    PRESSURE_10_BAR = 21


ZONT_BINARY_SENSORS = (
    ZontAnalogType.DOOR_SENSOR, ZontAnalogType.MOTION_SENSOR_CONTROL,
    ZontAnalogType.SMOKE_SENSOR, ZontAnalogType.LEAK_SENSOR,
    ZontAnalogType.MOTION_SENSOR, ZontAnalogType.DIGITAL_INPUT,
    ZontAnalogType.DIGITAL_INPUT_NO, ZontAnalogType.DIGITAL_INPUT_NC
)

PLATFORMS = [
    'sensor',
    'binary_sensor',
    'switch',
    'button',
    'climate',
    'alarm_control_panel',
]

MIN_TEMP_AIR = 5
MAX_TEMP_AIR = 35
MIN_TEMP_GVS = 25
MAX_TEMP_GVS = 75
MIN_TEMP_FLOOR = 15
MAX_TEMP_FLOOR = 45
MATCHES_GVS = ('гвс', 'горяч', 'вода', 'бкн', 'гидро', 'подача')
MATCHES_FLOOR = ('пол', 'тёплый',)
MODE_BOILER_NAMES = ['газ',  'электри', 'котёл', 'котел', 'котл']

HEATING_MODES = {
    'комфорт': 'mdi:emoticon-happy-outline',
    'эко': 'mdi:leaf-circle-outline',
    'лето': 'mdi:weather-sunny',
    'расписание': 'mdi:clock-outline',
    'выкл': 'mdi:power',
    'тишина': 'mdi:sleep',
    'дома': 'mdi:home-outline',
    'не дома': 'mdi:home-off-outline',
    'гвс': 'mdi:water-boiler',
}

ZONT_UNITS = {
    0: UnitOfElectricPotential.VOLT,
    1: 'kΩ',
    2: UnitOfPressure.BAR,
    3: UnitOfSpeed.KILOMETERS_PER_HOUR,
    4: REVOLUTIONS_PER_MINUTE,
    5: UnitOfVolume.LITERS,
    6: UnitOfVolumeFlowRate.LITERS_PER_HOUR,
    7: PERCENTAGE,
    8: None,
}

PERCENT_BATTERY = {
    3.1: 95,
    3.0: 90,
    2.9: 80,
    2.8: 70,
    2.7: 60,
    2.6: 50,
    2.5: 40,
    2.4: 30,
    2.3: 20,
    2.2: 10,
    2.1: 5,
}