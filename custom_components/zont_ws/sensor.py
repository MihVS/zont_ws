import logging
from functools import cached_property

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature, TEMPERATURE, PERCENTAGE, PRESSURE, UnitOfPressure
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
    WS_KEY_ERR_BOILER
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
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.NTC_TEMP_SENSOR | ZontType.DS18_TEMP_SENSOR:
                coordinator.ids_for_update.append(control_id)
                unique_id = f'{entry_id}{control_id}-temperature'
                unit = UnitOfTemperature.CELSIUS
                sens.append(ZontSensorTemperature(
                    coordinator, control_state, unique_id, unit)
                )
            case ZontType.CSH_ADAPTER:
                coordinator.ids_for_update.append(control_id)
                if control_state.get(WS_KEY_WATER_BOILER) is not None:
                    unique_id_water = (f'{entry_id}{control_id}'
                                       f'-temperature_water')
                    unit_water = UnitOfTemperature.CELSIUS
                    sens.append(ZontSensorTemperatureWater(
                        coordinator, control_state, unique_id_water,
                        unit_water, prefix='(теплоноситель)')
                    )
                if control_state.get(WS_KEY_DHW_BOILER) is not None:
                    unique_id_dhw = f'{entry_id}{control_id}-temperature_dhw'
                    unit_dhw = UnitOfTemperature.CELSIUS
                    sens.append(ZontSensorTemperatureDHW(
                        coordinator, control_state, unique_id_dhw, unit_dhw,
                        prefix='(ГВС)')
                    )
                if control_state.get(WS_KEY_MODUL_BOILER) is not None:
                    unique_id_modul = f'{entry_id}{control_id}-modul'
                    unit_modul = PERCENTAGE
                    sens.append(ZontSensorModul(
                        coordinator, control_state, unique_id_modul,
                        unit_modul, prefix='(модуляция)')
                    )
                if control_state.get(WS_KEY_PRESS_BOILER) is not None:
                    unique_id_press = f'{entry_id}{control_id}-press'
                    unit_press = UnitOfPressure.BAR
                    sens.append(ZontSensorPressBoiler(
                        coordinator, control_state, unique_id_press,
                        unit_press, prefix='(давление)')
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
        for sensor in sens:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                sensor.unique_id)
        if sens:
            async_add_entities(sens)
            _LOGGER.debug(f'Added sensors: {sens}')


class ZontSensor(CoordinatorEntity, SensorEntity):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str,
                 unit: str | None = None,
                 prefix: str = '') -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME) + prefix
        self._unique_id = unique_id
        self._unit = unit
        self._attr_device_info = coordinator.get_devices_info()

    @cached_property
    def name(self) -> str:
        return self._name

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id

    def __repr__(self) -> str:
        if not self.hass:
            return (f'<Sensor entity '
                    f'{self._coord.zont_info.model}-{self.name}>')
        return super().__repr__()


class ZontSensorTemperature(ZontSensor):

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_TEMPERATURE)

    @cached_property
    def device_class(self) -> str | None:
        return TEMPERATURE


class ZontSensorTemperatureWater(ZontSensorTemperature):

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_WATER_BOILER)


class ZontSensorTemperatureDHW(ZontSensorTemperature):

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_DHW_BOILER)


class ZontSensorModul(ZontSensor):

    _attr_icon = 'mdi:fire'

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_MODUL_BOILER)


class ZontSensorPressBoiler(ZontSensor):

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_PRESS_BOILER)

    @cached_property
    def device_class(self) -> str | None:
        return PRESSURE


class ZontSensorState(ZontSensor):

    _attr_icon = 'mdi:water-boiler'

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        state_value = control_state.get(WS_KEY_STATE_BOILER)
        match state_value:
            case 0:
                return 'off'
            case 1:
                return 'on'
            case 2:
                return 'error'


class ZontSensorErrorCode(ZontSensor):

    _attr_icon = 'mdi:wrench-outline'

    @property
    def native_value(self) -> float | str:
        """Return the value reported by the sensor."""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_ERR_BOILER)

