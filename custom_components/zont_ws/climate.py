import logging

from homeassistant.components.climate import (
    HVACMode, ClimateEntity, ClimateEntityFeature, PRESET_NONE
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator, DOMAIN
from .const import (
    WS_KEY_TYPE, ZontType, MAX_TEMP_AIR, MIN_TEMP_AIR, WS_KEY_NAME,
    ENTRIES, CURRENT_ENTITY_IDS, MATCHES_GVS, MIN_TEMP_GVS,
    MAX_TEMP_GVS, MATCHES_FLOOR, MIN_TEMP_FLOOR, MAX_TEMP_FLOOR,
    WS_KEY_MODE_ID, WS_KEY_MODE, WS_KEY_CURRENT_TEMP, WS_KEY_TARGET_TEMP,
    DELTA_KELVINS
)
from .core.exceptions import (
    TemperatureOutOfRangeError, SetPresetModeError, SetHvacModeError
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    thermostats = []
    for control_id, control_state in coordinator.data.items():
        if not isinstance(control_state, dict):
            continue
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.HEATING_CIRCUIT:
                coordinator.ids_for_update.append(control_id)
                unique_id = f'{entry_id}{control_id}-thermostat'
                thermostats.append(ZontClimateEntity(
                    coordinator, control_id, unique_id)
                )
    for thermostat in thermostats:
        hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
            thermostat.unique_id)
    if thermostats:
        async_add_entities(thermostats)
        _LOGGER.debug(f'Added thermostats: {thermostats}')


class ZontClimateEntity(CoordinatorEntity, ClimateEntity):
    """Базовый класс для климата zont"""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = MAX_TEMP_AIR
    _attr_min_temp = MIN_TEMP_AIR
    _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.PRESET_MODE
    )
    _enable_turn_on_off_backwards_compatibility: bool = False

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_id: int,
                 unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
        self._control_id = control_id
        self._control_state = coordinator.data.get(control_id)
        self._name = self._control_state.get(WS_KEY_NAME)
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()
        self._attr_target_temperature_step = 0.5
        self._attr_min_temp, self._attr_max_temp = (
            self.get_min_max_values_temp(self._name))

    @staticmethod
    def get_min_max_values_temp(circuit_name: str) -> tuple[float, float]:
        """
        Getting the maximum and minimum temperatures
        by the name of the heating circuit.
        """
        val_min, val_max = MIN_TEMP_AIR, MAX_TEMP_AIR
        circuit_name = circuit_name.lower().strip()
        if any([x in circuit_name for x in MATCHES_GVS]):
            val_min, val_max = MIN_TEMP_GVS, MAX_TEMP_GVS
        elif any([x in circuit_name for x in MATCHES_FLOOR]):
            val_min, val_max = MIN_TEMP_FLOOR, MAX_TEMP_FLOOR
        return val_min, val_max

    @property
    def preset_modes(self) -> list[str] | None:
        _preset_modes = []
        for control_id, control_state in self._coord.data.items():
            if not isinstance(control_state, dict):
                continue
            if control_state.get(WS_KEY_TYPE) == ZontType.MODE:
                _preset_modes.append(control_state[WS_KEY_NAME])
        _preset_modes.append(PRESET_NONE)
        return _preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        control_state = self._coord.data.get(self._control_id)
        heating_mode_id = control_state[WS_KEY_MODE_ID]
        heating_mode = self._coord.data.get(heating_mode_id)
        if heating_mode:
            return heating_mode[WS_KEY_NAME]
        return PRESET_NONE

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        control_state = self._coord.data.get(self._control_id)
        return control_state.get(WS_KEY_MODE)

    @property
    def name(self) -> str:
        return self._name

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        control_state =  self._coord.data.get(self._control_id)
        return control_state.get(WS_KEY_CURRENT_TEMP)

    @property
    def target_temperature(self) -> float:
        control_state = self._coord.data.get(self._control_id)
        return control_state.get(WS_KEY_TARGET_TEMP)

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @staticmethod
    def conver_to_kelvins(value: float) -> int:
        value = int(value * 10)
        return DELTA_KELVINS + value

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        set_temp = float(kwargs.get('temperature'))
        convert_set_temp = self.conver_to_kelvins(set_temp)
        if self._attr_min_temp <= set_temp <= self._attr_max_temp:
            _LOGGER.debug(f'{self.name} is changing temperature by {convert_set_temp}')
            await self._coord.zont_ws_api.send_command(
                self._control_id, convert_set_temp
            )
        else:
            raise TemperatureOutOfRangeError(
                f'Unacceptable temperature value: {set_temp}. '
                f'Set the temperature between {self._attr_min_temp} '
                f'and {self._attr_max_temp} inclusive.'
            )

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        raise SetPresetModeError(
            'Changing the preset mode is not supported by the device.'
        )

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        raise SetHvacModeError(
            'Changing the mode is not supported by the device.'
        )

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Climate entity {self.name}>"
        return super().__repr__()
