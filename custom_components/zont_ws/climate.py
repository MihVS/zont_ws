# import asyncio
# import logging
#
# from homeassistant.components.climate import (
#     HVACMode, ClimateEntity, ClimateEntityFeature, HVACAction, PRESET_NONE
# )
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import UnitOfTemperature
# from homeassistant.core import HomeAssistant, callback
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.update_coordinator import CoordinatorEntity
# from . import ZontCoordinator, DOMAIN
# from .const import (
#     WS_KEY_TYPE, ZontType, MAX_TEMP_AIR, MIN_TEMP_AIR, WS_KEY_ID, WS_KEY_NAME,
#     ENTRIES, CURRENT_ENTITY_IDS, PLUS, PRO, MATCHES_GVS, MIN_TEMP_GVS,
#     MAX_TEMP_GVS, MATCHES_FLOOR, MIN_TEMP_FLOOR, MAX_TEMP_FLOOR,
#     WS_KEY_MODE_ID, WS_KEY_MODE, WS_KEY_CURRENT_TEMP, WS_KEY_TARGET_TEMP
# )
# from .core.exceptions import TemperatureOutOfRangeError, SetHvacModeError
# from .core.zont_ws_api import ZontWsApi
#
# _LOGGER = logging.getLogger(__name__)
#
#
# async def async_setup_entry(
#         hass: HomeAssistant,
#         config_entry: ConfigEntry,
#         async_add_entities: AddEntitiesCallback
# ) -> None:
#     entry_id = config_entry.entry_id
#
#     coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]
#
#     for control_id, control_state in coordinator.zont_data.controls.items():
#         thermostats = []
#         type_control = control_state.get(WS_KEY_TYPE)
#         match type_control:
#             case ZontType.HEATING_CIRCUIT:
#                 unique_id = f'{entry_id}{control_id}-thermostat'
#                 thermostats.append(ZontClimateEntity(
#                     coordinator, control_state, unique_id)
#                 )
#         for thermostat in thermostats:
#             hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
#                 thermostat.unique_id)
#         if thermostats:
#             async_add_entities(thermostats)
#             _LOGGER.debug(f'Added thermostats: {thermostats}')
#
#
# class ZontClimateEntity(CoordinatorEntity, ClimateEntity):
#     """Базовый класс для климата zont"""
#
#     _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
#     _attr_max_temp = MAX_TEMP_AIR
#     _attr_min_temp = MIN_TEMP_AIR
#     _attr_supported_features = (
#             ClimateEntityFeature.TARGET_TEMPERATURE |
#             ClimateEntityFeature.PRESET_MODE
#     )
#     _enable_turn_on_off_backwards_compatibility: bool = False
#
#     def __init__(self,
#                  coordinator: ZontCoordinator,
#                  control_state: dict,
#                  unique_id: str
#     ) -> None:
#         super().__init__(coordinator)
#         self._coord = coordinator
#         self._control_id = control_state.get(WS_KEY_ID)
#         self._control_state = control_state
#         self._name = control_state.get(WS_KEY_NAME)
#         self._unique_id = unique_id
#         self._attr_device_info = coordinator.get_devices_info()
#         self._attr_target_temperature_step = 0.1
#         self._attr_min_temp, self._attr_max_temp = (
#             self.get_min_max_values_temp(self._name))
#
#     @staticmethod
#     def get_min_max_values_temp(circuit_name: str) -> tuple[float, float]:
#         """
#         Getting the maximum and minimum temperatures
#         by the name of the heating circuit.
#         """
#         val_min, val_max = MIN_TEMP_AIR, MAX_TEMP_AIR
#         circuit_name = circuit_name.lower().strip()
#         if any([x in circuit_name for x in MATCHES_GVS]):
#             val_min, val_max = MIN_TEMP_GVS, MAX_TEMP_GVS
#         elif any([x in circuit_name for x in MATCHES_FLOOR]):
#             val_min, val_max = MIN_TEMP_FLOOR, MAX_TEMP_FLOOR
#         return val_min, val_max
#
#     @property
#     def preset_modes(self) -> list[str] | None:
#         _preset_modes = []
#         circuit_modes = self._coord.zont_data.circuit_modes
#         for circuit_mode_id, circuit_mode in circuit_modes.items():
#             _preset_modes.append(circuit_mode[WS_KEY_NAME])
#         _preset_modes.append(PRESET_NONE)
#         return _preset_modes
#
#     @property
#     def preset_mode(self) -> str | None:
#         heating_mode_id = self._control_state[WS_KEY_MODE_ID]
#         heating_mode = self._coord.zont_data.circuit_modes.get(heating_mode_id)
#         if heating_mode is not None:
#             return heating_mode[WS_KEY_NAME]
#         return PRESET_NONE
#
#     @property
#     def hvac_mode(self) -> HVACMode | None:
#         """Return hvac operation ie. heat, cool mode."""
#         return self._control_state.get(WS_KEY_MODE)
#
#     @property
#     def name(self) -> str:
#         return self._name
#
#     @property
#     def temperature_unit(self) -> str:
#         return UnitOfTemperature.CELSIUS
#
#     @property
#     def current_temperature(self) -> float:
#         return self._control_state.get(WS_KEY_CURRENT_TEMP)
#
#     @property
#     def target_temperature(self) -> float:
#         return self._control_state.get(WS_KEY_TARGET_TEMP)
#
#     @property
#     def unique_id(self) -> str:
#         return self._unique_id
#
#     async def async_set_temperature(self, **kwargs) -> None:
#         """Set new target temperature."""
#         set_temp = kwargs.get('temperature')
#         if self._attr_min_temp <= set_temp <= self._attr_max_temp:
#             await self._coord.zont_ws_api.send_command(
#
#             )
#         else:
#             raise TemperatureOutOfRangeError(
#                 f'Недопустимое значение температуры: {set_temp}. '
#                 f'Задайте температуру в пределах от {self._attr_min_temp} '
#                 f'до {self._attr_max_temp} включительно.'
#             )
#
#     async def async_set_preset_mode(self, preset_mode):
#         """Set new target preset mode."""
#         heating_mode = self._zont.get_heating_mode_by_name(
#             self._device, preset_mode
#         )
#         model = self._device.device_info.model
#         if heating_mode is not None:
#             if self._device.device_info.model in MODELS_THERMOSTAT_ZONT:
#                 await self._zont.set_heating_mode_all_circuits(
#                     device=self._device,
#                     heating_mode=heating_mode
#                 )
#             elif PLUS in model.lower() or PRO in model.lower():
#                 await self._zont.set_heating_mode(
#                     device=self._device,
#                     circuit=self._circuit,
#                     heating_mode_id=heating_mode.id
#                 )
#             else:
#                 await self._zont.set_heating_mode_v1(
#                     self._device, self._circuit, heating_mode.id)
#         else:
#             await self._zont.set_target_temperature(
#                 device=self._device,
#                 circuit=self._circuit,
#                 target_temp=self._circuit.target_temp
#             )
#             self._circuit.current_mode = None
#         await asyncio.sleep(TIME_OUT_REQUEST)
#         await self.coordinator.async_request_refresh()
#
#     def __repr__(self) -> str:
#         if not self.hass:
#             return f"<Climate entity {self.name}>"
#         return super().__repr__()
#
#     def set_hvac_mode(self, hvac_mode):
#         """Set new target hvac mode."""
#         raise SetHvacModeError(
#             'Изменение HVAC не поддерживается ZONT. '
#             'Контур управляется котлом.'
#         )
#
#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Обработка обновлённых данных от координатора"""
#         self._device: DeviceZONT = self.coordinator.zont.get_device(
#             self._device.id
#         )
#         self._circuit = self._zont.get_circuit(
#             self._device, self._circuit.id
#         )
#         self.async_write_ha_state()