import logging
from functools import cached_property

from homeassistant.components.binary_sensor import (
    BinarySensorEntity, BinarySensorDeviceClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_TYPE, ZontType, WS_KEY_STYPE,
    ZontWebElmType, WS_KEY_ID, WS_KEY_NAME, WS_KEY_STATE, ZontAnalogType,
    WS_KEY_TRIGGERED, ZONT_BINARY_SENSORS, WS_KEY_AVAILABLE, WS_KEY_FAILURE,
    ZONT_BINARY_SENSORS_RDIO, RadioType, WS_KEY_SERVICE_CMD_RESPONSE,
    ZontSysCommand
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    binary_sensors = []
    for control_id, control_state in coordinator.data.items():
        if not isinstance(control_state, dict):
            continue
        if control_id == WS_KEY_SERVICE_CMD_RESPONSE:
            lan_info = control_state.get(ZontSysCommand.NETWORK_INFO)
            _LOGGER.debug(f'LAN info: {lan_info}')
            if check_lan(lan_info):
                coordinator.sys_for_update.append(ZontSysCommand.NETWORK_INFO)
                unique_id = f'{entry_id}{control_id}-LAN-info'
                binary_sensors.append(ZontBinarySensorNetwork(
                    coordinator, unique_id, 'Локальная сеть')
                )
            server_info = control_state.get(ZontSysCommand.SERVER_INFO)
            _LOGGER.debug(f'Server info: {server_info}')
            if check_server(server_info):
                coordinator.sys_for_update.append(ZontSysCommand.NETWORK_INFO)
                unique_id = f'{entry_id}{control_id}-server-info'
                binary_sensors.append(ZontBinarySensorCloudConnect(
                    coordinator, unique_id, 'Облако ZONT')
                )

        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.HEATING_CIRCUIT:
                coordinator.ids_for_update.append(control_id)
                unique_id = f'{entry_id}{control_id}-failure'
                binary_sensors.append(ZontBinarySensorFailure(
                    coordinator, control_state, unique_id,
                    prefix='(Авария)')
                )
            case ZontType.WEB_ELEMENT:
                type_web_elm = control_state.get(WS_KEY_STYPE)
                if type_web_elm == ZontWebElmType.BINARY:
                    coordinator.ids_for_update.append(control_id)
                    unique_id = f'{entry_id}{control_id}-binary_web_elm'
                    binary_sensors.append(ZontBinarySensor(
                        coordinator, control_state, unique_id)
                    )
            case ZontType.ANALOG_INPUT:
                type_analog = control_state.get(WS_KEY_STYPE)
                if type_analog in ZONT_BINARY_SENSORS:
                    coordinator.ids_for_update.append(control_id)
                    unique_id = f'{entry_id}{control_id}-binary_analog'
                    binary_sensors.append(ZontBinarySensorAnalog(
                        coordinator, control_state, unique_id)
                    )
            case ZontType.RADIO_SENSOR:
                type_radio_sensor = control_state.get(WS_KEY_STYPE)
                if type_radio_sensor in ZONT_BINARY_SENSORS_RDIO:
                    coordinator.ids_for_update.append(control_id)
                    unique_id = f'{entry_id}{control_id}-binary_radio'
                    binary_sensors.append(ZontBinarySensorAnalog(
                        coordinator, control_state, unique_id)
                    )
    for binary_sensor in binary_sensors:
        hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
            binary_sensor.unique_id)
    if binary_sensors:
        async_add_entities(binary_sensors)
        _LOGGER.debug(f'Added binary sensors: {binary_sensors}')

def check_lan(date: str):
    if date:
        if len(date.split(' ')) == 5:
            _LOGGER.debug('check_lan: True')
            return True
    _LOGGER.debug('check_lan: False')
    return False

def check_server(date: str):
    if date:
        if len(date.split(' ')) == 4:
            _LOGGER.debug('check_server: True')
            return True
    _LOGGER.debug('check_server: False')
    return False


class ZontBinarySensor(CoordinatorEntity, BinarySensorEntity):

    _ws_key = WS_KEY_STATE

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str,
                 prefix: str = '') -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME) + prefix
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()

    @cached_property
    def name(self) -> str:
        return self._name

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        control_state = self._coord.data.get(self._control_id)
        if control_state:
            return bool(control_state.get(self._ws_key))

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        control_state = self._coord.data.get(self._control_id)
        is_available = control_state.get(WS_KEY_AVAILABLE)
        if is_available is not None:
            return bool(control_state.get(WS_KEY_AVAILABLE))
        else:
            return self.coordinator.last_update_success

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Binary sensor entity {self.name}>"
        return super().__repr__()


class ZontBinarySensorFailure(ZontBinarySensor):

    _ws_key = WS_KEY_FAILURE
    _attr_icon = 'mdi:wrench'


class ZontBinarySensorExtension(ZontBinarySensor):

    _ws_key = WS_KEY_TRIGGERED


class ZontBinarySensorAnalog(ZontBinarySensorExtension):

    @cached_property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        control_state = self._coord.data.get(self._control_id)
        type_analog = control_state.get(WS_KEY_STYPE)
        match type_analog:
            case ZontAnalogType.DOOR_SENSOR:
                return BinarySensorDeviceClass.DOOR
            case ZontAnalogType.LEAK_SENSOR:
                return BinarySensorDeviceClass.MOISTURE
            case ZontAnalogType.SMOKE_SENSOR:
                return BinarySensorDeviceClass.SMOKE
            case ZontAnalogType.MOTION_SENSOR | ZontAnalogType.MOTION_SENSOR_CONTROL:
                return BinarySensorDeviceClass.MOTION
            case _:
                return None


class ZontBinarySensorRadio(ZontBinarySensorExtension):

    @cached_property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        control_state = self._coord.data.get(self._control_id)
        type_radio = control_state.get(WS_KEY_STYPE)
        match type_radio:
            case RadioType.LEAK_SENSOR:
                return BinarySensorDeviceClass.MOISTURE
            case RadioType.MOTION_SENSOR:
                return BinarySensorDeviceClass.MOTION
            case _:
                return None


class ZontBinarySensorService(CoordinatorEntity, BinarySensorEntity):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 unique_id: str,
                 name: str) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._name = name
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()

    @cached_property
    def name(self) -> str:
        return self._name

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id

    def __repr__(self) -> str:
        if not self.hass:
            return (f'<Sensor entity '
                    f'{self._coord.zont_info.model}-{self.name}>')
        return super().__repr__()


class ZontBinarySensorNetwork(ZontBinarySensorService):

    _unrecorded_attributes = frozenset({MATCH_ALL})

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = int(self.coordinator.data[
                        WS_KEY_SERVICE_CMD_RESPONSE][
                        ZontSysCommand.NETWORK_INFO].split(' ')[4])
        return bool(value)

    @cached_property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(WS_KEY_SERVICE_CMD_RESPONSE, {})
        lan_info = data.get(ZontSysCommand.NETWORK_INFO, '')

        parts = lan_info.split(' ')

        return {
            'available': parts[4] if len(parts) > 4 else 'unknown',
            'mac': parts[0] if len(parts) > 0 else 'unknown',
            'ip': parts[1] if len(parts) > 1 else 'unknown',
            'mask': parts[2] if len(parts) > 2 else 'unknown',
            'gateway': parts[3] if len(parts) > 3 else 'unknown',
        }


class ZontBinarySensorCloudConnect(ZontBinarySensorService):

    _unrecorded_attributes = frozenset({MATCH_ALL})

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = int(self.coordinator.data[
                        WS_KEY_SERVICE_CMD_RESPONSE][
                        ZontSysCommand.SERVER_INFO].split(' ')[0])
        return bool(value)

    @cached_property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this entity."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def extra_state_attributes(self):
        type_of_connect = ['UNKNOWN', 'GSM', 'Wi-Fi', 'Ethernet']
        data = self.coordinator.data.get(WS_KEY_SERVICE_CMD_RESPONSE, {})
        lan_info = data.get(ZontSysCommand.SERVER_INFO, '')

        parts = lan_info.split(' ')
        connected_via = type_of_connect[0]
        for i in range(1, 4):
            if parts[i] == '1':
                connected_via = type_of_connect[i]
                break

        return {
            'available': parts[0] if len(parts) > 0 else 'unknown',
            'connected_via': connected_via
        }
