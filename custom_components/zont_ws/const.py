DOMAIN = 'zont_ws'
MANUFACTURER = 'MicroLine'
CONFIGURATION_URL = 'https://my.zont.online/'

ENTRIES = 'entries'
CURRENT_ENTITY_IDS = 'current_entity_ids'

LOGIN_DEFAULT = 'admin'
PASSWORD_DEFAULT = 'admin'
URL_DEFAULT = 'https://192.168.1.40/ws'

TIME_UPDATE = 15
WS_TIMEOUT_REQUEST = 10
HEARTBEAT = 60

WS_KEY_USER = 'user'
WS_KEY_PASS = 'pass'
WS_KEY_AUTH = 'auth'
WS_AUTH_SUCCESS = 200
WS_AUTH_ERROR = 401
WS_KEY_REQUEST_IDS = 'req_ids'
WS_KEY_IDS = 'ids'
WS_KEY_ID = 'id'
WS_KEY_RESPONSE_ID = 'Id'
WS_KEY_REQUEST_STATE = 'req_state'
WS_KEY_TYPE = 'type'
WS_KEY_NAME = 'name'
WS_KEY_STYPE = 'stype'
WS_KEY_CMD = 'cmd'
WS_KEY_CMD_RESULT = 'cmdres'
WS_KEY_SERVICE_CMD = 'scmd'
WS_KEY_SERVICE_CMD_RESULT = 'scmdres'
WS_KEY_TEMPERATURE = 't'
WS_KEY_AVAILABLE = 'a'


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
    NTC_TEMP_SENSOR = 27
    ANY = 255


PLATFORMS = [
    'sensor',
    # 'binary_sensor',
    # 'switch',
    # 'button',
    # 'climate',
    # 'alarm_control_panel',
    # 'device_tracker'
]