import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity, BinarySensorDeviceClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_TYPE, ZontType, WS_KEY_STYPE,
    ZontWebElmType, WS_KEY_ID, WS_KEY_NAME, WS_KEY_STATE, ZontAnalogType,
    WS_KEY_TRIGGERED, ZONT_BINARY_SENSORS, WS_KEY_AVAILABLE,
    ZONT_BINARY_SENSORS_RDIO, RadioType
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    for control_id, control_state in coordinator.data.items():
        binary_sensors = []
        if not isinstance(control_state, dict):
            continue
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
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


class ZontBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME)
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        control_state = self._coord.data.get(self._control_id)
        if control_state:
            return bool(control_state.get(WS_KEY_STATE))

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


class ZontBinarySensorExtension(ZontBinarySensor):

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        control_state = self._coord.data.get(self._control_id)
        if control_state:
            return bool(control_state.get(WS_KEY_TRIGGERED))


class ZontBinarySensorAnalog(ZontBinarySensorExtension):

    @property
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

    @property
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
