import asyncio
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity, AlarmControlPanelEntityFeature,
    AlarmControlPanelState
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_ID, WS_KEY_TYPE, ZontType,
    WS_KEY_NAME, WS_KEY_TRIGGERED, WS_KEY_STATE, COMMAND_ON, COMMAND_OFF,
    COUNTER_REPEAT, TIME_OUT_REPEAT
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    alarms = []
    for control_id, control_state  in coordinator.data.items():
        if not isinstance(control_state, dict):
            continue
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.SECURITY_ZONE:
                coordinator.ids_for_update.append(control_id)
                unique_id = f'{entry_id}{control_id}-security_zone'
                alarms.append(ZontAlarm(
                    coordinator, control_state, unique_id)
                )
    for alarm in alarms:
        hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
            alarm.unique_id)
    if alarms:
        async_add_entities(alarms)
        _LOGGER.debug(f'Added alarm control panels: {alarms}')


class ZontAlarmBase(CoordinatorEntity, AlarmControlPanelEntity):

    def __init__(self, coordinator: ZontCoordinator) -> None:
        super().__init__(coordinator)
        self._coord: ZontCoordinator = coordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._coord.zont_ws_api.is_connected:
            return False
        return True


class ZontAlarm(ZontAlarmBase):

    _attr_code_format = None
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY |
        AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str) -> None:
        super().__init__(coordinator)
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME)
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()
        self._is_enabling = False
        self._is_disabling = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Alarm entity {self.name}>"
        return super().__repr__()

    @property
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        """Return the list of supported features."""
        return self._attr_supported_features

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        control_state = self._coord.data.get(self._control_id, {})
        if control_state.get(WS_KEY_TRIGGERED):
            return AlarmControlPanelState.TRIGGERED
        if self._is_enabling:
            return AlarmControlPanelState.ARMING
        if self._is_disabling:
            return AlarmControlPanelState.DISARMING
        if control_state.get(WS_KEY_STATE):
            return AlarmControlPanelState.ARMED_AWAY
        else:
            return AlarmControlPanelState.DISARMED

    async def _repeat_check_state(self, command: int):
        """
        We update the status of the protected area
        until we receive a status change.
        """
        counter = COUNTER_REPEAT
        while counter > 0:
            counter -= 1
            if command:
                if not self._is_enabling:
                    return
            else:
                if not self._is_disabling:
                    return
            await self._coord.zont_ws_api.get_state(self._control_id)
            await asyncio.sleep(1)
            control_state = self._coord.data.get(self._control_id, {})
            state_control = control_state.get(WS_KEY_STATE)
            if command == state_control:
                self._is_enabling = False
                self._is_disabling = False
                self.async_write_ha_state()
                _LOGGER.debug(f'Alarm zone {self._name} is updated successful.')
                return
            await asyncio.sleep(TIME_OUT_REPEAT)
            _LOGGER.debug(f'Try update alarm state for {self._name} '
                          f'({self._coord.zont_ws_api.url})')

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        self._is_disabling = True
        self._is_enabling = False
        await self._coord.zont_ws_api.send_command(
            self._control_id, COMMAND_OFF
        )
        await self._repeat_check_state(COMMAND_OFF)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm home command."""
        self._is_enabling = True
        self._is_disabling = False
        await self._coord.zont_ws_api.send_command(
            self._control_id, COMMAND_ON
        )
        await self._repeat_check_state(COMMAND_ON)
