import logging
from functools import cached_property

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_ID, WS_KEY_TYPE, ZontType,
    WS_KEY_NAME, WS_KEY_TEMPERATURE
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
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.NTC_TEMP_SENSOR | ZontType.DS18_TEMP_SENSOR:
                coordinator.zont_sensors_ids.append(control_id)
                unique_id = f'{entry_id}{control_id}-temperature'
                unit = UnitOfTemperature.CELSIUS
                sens.append(ZontSensorTemperature(
                    coordinator, control_state, unique_id, unit)
                )
        for sensor in sens:
            hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
                sensor.unique_id)
        if sens:
            async_add_entities(sens)
            _LOGGER.debug(f'Added sensors: {sens}')


class ZontSensorTemperature(CoordinatorEntity, SensorEntity):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str,
                 unit: str) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME)
        self._unique_id = unique_id
        self._unit = unit
        self._attr_device_info = coordinator.get_devices_info()

    @cached_property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        return SensorStateClass.MEASUREMENT

    @cached_property
    def name(self) -> str:
        return self._name

    @property
    def native_value(self) -> float | str:
        """Возвращает состояние сенсора"""
        control_state = self._coord.data.get(self._control_id, {})
        return control_state.get(WS_KEY_TEMPERATURE)

    @cached_property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @cached_property
    def unique_id(self) -> str:
        return self._unique_id

    @cached_property
    def device_class(self) -> str | None:
        return TEMPERATURE

    def __repr__(self) -> str:
        if not self.hass:
            return (f'<Sensor entity '
                    f'{self._coord.zont_info.model}-{self.name}>')
        return super().__repr__()
