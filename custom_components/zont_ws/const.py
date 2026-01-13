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

ZONT_TYPE_ANALOG_INPUT = 0
ZONT_TYPE_DS18_TEMP_SENSOR = 1
ZONT_TYPE_SECURITY_ZONE = 2
ZONT_TYPE_CSH_ADAPTER = 6
ZONT_TYPE_RADIO_SENSOR = 8
ZONT_TYPE_WEB_ELEMENT = 10
ZONT_TYPE_RELAY = 14
ZONT_TYPE_MIXER = 15
ZONT_TYPE_HEATING_CIRCUIT = 16
ZONT_TYPE_PUMP = 17
ZONT_TYPE_NTC_TEMP_SENSOR = 27
ZONT_TYPE_ANY = 255

PLATFORMS = [
    # 'sensor',
    # 'binary_sensor',
    # 'switch',
    # 'button',
    # 'climate',
    # 'alarm_control_panel',
    # 'device_tracker'
]