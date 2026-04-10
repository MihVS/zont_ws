import logging
from functools import cached_property

from homeassistant.components.sensor import (
    SensorEntity, SensorStateClass, SensorDeviceClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature, PERCENTAGE, UnitOfPressure,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT, MATCH_ALL
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_ID, WS_KEY_TYPE, ZontType,
    WS_KEY_NAME, WS_KEY_TEMPERATURE, WS_KEY_WATER_BOILER, WS_KEY_DHW_BOILER,
    WS_KEY_MODUL_BOILER, WS_KEY_PRESS_BOILER, WS_KEY_STATE_BOILER,
    WS_KEY_ERR_BOILER, WS_KEY_STYPE, ZONT_BINARY_SENSORS, ZONT_UNITS,
    WS_KEY_UNIT, WS_KEY_VALUE, PERCENT_BATTERY, WS_KEY_HUMIDITY,
    WS_KEY_BATTERY, ZontAnalogType, RadioType, WS_KEY_RSSI, WS_KEY_AVAILABLE,
    WS_KEY_SERVICE_CMD_RESPONSE, ZontSysCommand
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    for control_id, control_state  in coordinator.data.items():
        sens = []
        if not isinstance(control_state, dict):
            continue
        if control_id == WS_KEY_SERVICE_CMD_RESPONSE:
            gsm_info = control_state.get(ZontSysCommand.GSM_INFO)
            _LOGGER.debug(f'GSM info: {gsm_info}')
            if check_gsm(gsm_info):
                coordinator.sys_for_update.append(ZontSysCommand.GSM_INFO)
                unique_id = f'{entry_id}{control_id}-gsm_level'
                sens.append(ZontSensorGSMLevel(coordinator, unique_id))

            wifi_info = control_state.get(ZontSysCommand.WIFI_INFO)
            _LOGGER.debug(f'WI-FI info: {wifi_info}')
            if check_wifi(wifi_info):
                coordinator.sys_for_update.append(ZontSysCommand.WIFI_INFO)
                unique_id = f'{entry_id}{control_id}-wifi_level'
                sens.append(ZontSensorWIFILevel(coordinator, unique_id))

        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.NTC_TEMP_SENSOR | ZontType.DS18_TEMP_SENSOR:
                coordinator.ids_for_update.append(control_id)

                unique_id = f'{entry_id}{control_id}-temperature'
                sens.append(ZontSensorTemperature(
                    coordinator, control_state, unique_id)
                )
            case ZontType.CSH_ADAPTER:
                coordinator.ids_for_update.append(control_id)

                if control_state.get(WS_KEY_WATER_BOILER) is not None:
                    unique_id_water = (f'{entry_id}{control_id}'
                                       f'-temperature_water')
                    sens.append(ZontSensorTemperatureWater(
                        coordinator, control_state, unique_id_water,
                        prefix='(теплоноситель)')
                    )
                if control_state.get(WS_KEY_DHW_BOILER) is not None:
                    unique_id_dhw = f'{entry_id}{control_id}-temperature_dhw'
                    sens.append(ZontSensorTemperatureDHW(
                        coordinator, control_state, unique_id_dhw,
                        prefix='(ГВС)')
                    )
                if control_state.get(WS_KEY_MODUL_BOILER) is not None:
                    unique_id_modul = f'{entry_id}{control_id}-modul'
                    sens.append(ZontSensorModul(
                        coordinator, control_state, unique_id_modul,
                        prefix='(модуляция)')
                    )
                if control_state.get(WS_KEY_PRESS_BOILER) is not None:
                    unique_id_press = f'{entry_id}{control_id}-press'
                    sens.append(ZontSensorPressBoiler(
                        coordinator, control_state, unique_id_press,
                        prefix='(давление)')
                    )
                if control_state.get(WS_KEY_STATE_BOILER) is not None:
                    unique_id_state = f'{entry_id}{control_id}-state'
                    sens.append(ZontSensorState(
                        coordinator, control_state, unique_id_state,
                        prefix='(состояние)')
                    )
                unique_id_error = f'{entry_id}{control_id}-error'
                sens.append(ZontSensorErrorCode(
                    coordinator, control_state, unique_id_error,
                    prefix='(Код ошибки)')
                )
            case ZontType.ANALOG_INPUT:
                coordinator.ids_for_update.append(control_id)

                if not control_state.get(WS_KEY_STYPE) in ZONT_BINARY_SENSORS:
                    unique_id = f'{entry_id}{control_id}-analog'
                    sens.append(ZontSensorAnalog(
                        coordinator, control_state, unique_id)
                    )
            case ZontType.RADIO_SENSOR:
                type_radio_sensor = control_state.get(WS_KEY_STYPE)
                match type_radio_sensor:
                    case RadioType.RADIO_THERMOMETER | RadioType.EXTERNAL_TEMP_SENSOR:
                        coordinator.ids_for_update.append(control_id)

                        unique_id_temp = f'{entry_id}{control_id}-temperature'
                        sens.append(ZontSensorTemperature(
                            coordinator, control_state, unique_id_temp)
                        )
                        unique_id_bat = f'{entry_id}{control_id}-battery'
                        sens.append(ZontSensorBattery(
                            coordinator, control_state, unique_id_bat)
                        )
                        unique_id_rssi = f'{entry_id}{control_id}-rssi'
                        sens.append(ZontSensorRSSI(
                            coordinator, control_state, unique_id_rssi)
                        )
                    case RadioType.TEMP_HUMIDITY_SENSOR:
                        coordinator.ids_for_update.append(control_id)

                        unique_id_temp = f'{entry_id}{control_id}-temperature'
                        sens.append(ZontSensorTemperature(
                            coordinator, control_state, unique_id_temp)
                        )
                        coordinator.ids_for_update.append(control_id)
                        unique_id_humi = f'{entry_id}{control_id}-humidity'
                        sens.append(ZontSensorHumidity(
                            coordinator, control_state, unique_id_humi)
                        )
                        unique_id_bat = f'{entry_id}{control_id}-battery'
                        sens.append(ZontSensorBattery(
                            coordinator, control_state, unique_id_bat)
                        )
                        unique_id_rssi = f'{entry_id}{control_id}-rssi'
                        sens.append(ZontSensorRSSI(
                            coordinator, control_state, unique_id_rssi)
                        )
                    case RadioType.LEAK_SENSOR | RadioType.MOTION_SENSOR:
                        coordinator.ids_for_update.append(control_id)

                        unique_id_bat = f'{entry_id}{control_id}-battery'
                        sens.append(ZontSensorBattery(
                            coordinator, control_state, unique_id_bat)
                        )
                        unique_id_rssi = f'{entry_id}{control_id}-rssi'
                        sens.append(ZontSensorRSSI(
                            coordinator, control_state, unique_id_rssi)
                        )

        for sensor in sens:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                sensor.unique_id)
        if sens:
            async_add_entities(sens)
            _LOGGER.debug(f'Added sensors: {sens}')

def check_gsm(date: str):
    if date:
        if len(date.split(' ', maxsplit=2)) == 3:
            _LOGGER.debug('check_gsm: True')
            return True
    _LOGGER.debug('check_gsm: False')
    return False

def check_wifi(date: str):
    if date:
        _LOGGER.debug('check_wifi: True')
        return True
    _LOGGER.debug('check_wifi: False')
    return False

class ZontSensor(CoordinatorEntity, SensorEntity):

    _ws_key = WS_KEY_VALUE

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str,
                 prefix: str = '') -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_state.get(WS_KEY_ID)
        self._control_state = control_state
        self._name = control_state.get(WS_KEY_NAME) + prefix
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

    def get_value(self) -> int | float | str:
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(self._ws_key)

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        return self.get_value()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        control_state = self._coord.data.get(self._control_id)
        is_available = control_state.get(WS_KEY_AVAILABLE)
        if is_available is not None:
            return bool(control_state.get(WS_KEY_AVAILABLE))
        else:
            return self.coordinator.last_update_success


class ZontSensorMeasurement(ZontSensor):

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT


class ZontSensorTemperature(ZontSensorMeasurement):

    _ws_key = WS_KEY_TEMPERATURE

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return UnitOfTemperature.CELSIUS

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        return SensorDeviceClass.TEMPERATURE


class ZontSensorTemperatureWater(ZontSensorTemperature):

    _ws_key = WS_KEY_WATER_BOILER


class ZontSensorTemperatureDHW(ZontSensorTemperature):

    _ws_key = WS_KEY_DHW_BOILER


class ZontSensorModul(ZontSensorMeasurement):

    _attr_icon = 'mdi:fire'
    _ws_key = WS_KEY_MODUL_BOILER

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return PERCENTAGE


class ZontSensorPressBoiler(ZontSensorMeasurement):

    _ws_key = WS_KEY_PRESS_BOILER

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return UnitOfPressure.BAR

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        return SensorDeviceClass.PRESSURE


class ZontSensorState(ZontSensor):

    _attr_icon = 'mdi:water-boiler'
    _ws_key = WS_KEY_STATE_BOILER

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        state_value = self.get_value()
        match state_value:
            case 0:
                return 'off'
            case 1:
                return 'on'
            case 2:
                return 'error'


class ZontSensorErrorCode(ZontSensor):

    _attr_icon = 'mdi:wrench-outline'
    _ws_key = WS_KEY_ERR_BOILER


class ZontSensorAnalog(ZontSensorMeasurement):

    _ws_key = WS_KEY_VALUE

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        unit_of_sensor = self._control_state.get(WS_KEY_UNIT)
        return ZONT_UNITS.get(unit_of_sensor)

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        type_sensor = self._control_state.get(WS_KEY_STYPE)
        match type_sensor:
            case ZontAnalogType.ANALOG:
                return SensorDeviceClass.VOLTAGE
            case (ZontAnalogType.PRESSURE_5_BAR |
                  ZontAnalogType.PRESSURE_6_BAR |
                  ZontAnalogType.PRESSURE_10_BAR |
                  ZontAnalogType.PRESSURE_12_BAR):
                return SensorDeviceClass.PRESSURE
            case ZontAnalogType.HUMIDITY_SENSOR:
                return SensorDeviceClass.HUMIDITY
            case _:
                return None


class ZontSensorHumidity(ZontSensorMeasurement):

    _ws_key = WS_KEY_HUMIDITY

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return PERCENTAGE

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        return SensorDeviceClass.HUMIDITY


class ZontSensorBattery(ZontSensorMeasurement):

    _ws_key = WS_KEY_BATTERY

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        value = self.get_value()
        return self._convert_value_battery(value)

    @staticmethod
    def _convert_value_battery(value: float) -> int:
        """Converts the battery voltage to the charge level in %."""
        value = round(value, 1)
        if value > 3.1:
            return 100
        elif value < 2.1:
            return 0
        else:
            return PERCENT_BATTERY[value]

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return PERCENTAGE

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        return SensorDeviceClass.BATTERY


class ZontSensorRSSI(ZontSensorMeasurement):

    _ws_key = WS_KEY_RSSI

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @cached_property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the class of this entity."""
        return SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        value = self.get_value()
        return value / 2 - 73


class ZontSensorGSMLevel(CoordinatorEntity, SensorEntity):

    # _attr_icon = 'mdi: mdi:wifi-strength-4'

    def __init__(self, coordinator: ZontCoordinator, unique_id: str) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._name = 'Сигнал GSM'
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

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return PERCENTAGE

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        value = self.coordinator.data[
            WS_KEY_SERVICE_CMD_RESPONSE][ZontSysCommand.GSM_INFO].split(' ')[0]
        return int((int(value) / 31) * 100)


class ZontSensorWIFILevel(CoordinatorEntity, SensorEntity):

    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, coordinator: ZontCoordinator, unique_id: str) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._name = 'Сигнал WI-FI'
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

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return PERCENTAGE

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        value = int(self.coordinator.data[
            WS_KEY_SERVICE_CMD_RESPONSE][
            ZontSysCommand.WIFI_INFO].split(' ')[1])
        return self._rssi_to_percent(value)

    @property
    def icon(self) -> str:
        """Return the icon based on signal level."""
        signal_level = self.native_value
        if signal_level >= 80:
            return "mdi:wifi-strength-4"
        elif signal_level >= 60:
            return "mdi:wifi-strength-3"
        elif signal_level >= 40:
            return "mdi:wifi-strength-2"
        elif signal_level >= 20:
            return "mdi:wifi-strength-1"
        elif signal_level > 0:
            return "mdi:wifi-strength-outline"
        return "mdi:wifi-strength-off-outline"

    @staticmethod
    def _rssi_to_percent(value: int) -> int:
        if value == 0:
            return 0
        rssi = -value
        if rssi <= -100:
            return 1
        elif rssi >= -50:
            return 100
        else:
            return 2 * (rssi + 100)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(WS_KEY_SERVICE_CMD_RESPONSE, {})
        wifi_info = data.get(ZontSysCommand.WIFI_INFO, "")

        parts = wifi_info.split(' ')

        return {
            'available': parts[0] if len(parts) > 0 else 'unknown',
            'mac': parts[2] if len(parts) > 2 else 'unknown',
            'ip': parts[3] if len(parts) > 3 else 'unknown',
            'mask': parts[4] if len(parts) > 4 else 'unknown',
            'gate': parts[5] if len(parts) > 5 else 'unknown',
        }
