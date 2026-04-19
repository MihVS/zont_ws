import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_ID, WS_KEY_TYPE, ZontType,
    WS_KEY_NAME, COMMAND_ON, COMMAND_OFF, WS_KEY_STATE, ZontWebElmType,
    WS_KEY_STYPE
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    switches = []
    for control_id, control_state in coordinator.data.items():
        if not isinstance(control_state, dict):
            continue
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.WEB_ELEMENT:
                type_web_elm = control_state.get(WS_KEY_STYPE)
                if type_web_elm == ZontWebElmType.SWITCH:
                    coordinator.ids_for_update.append(control_id)
                    unique_id = f'{entry_id}{control_id}-switch'
                    switches.append(SwitchZont(
                        coordinator, control_state, unique_id)
                    )
    for switch in switches:
        hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
            switch.unique_id)
    if switches:
        async_add_entities(switches)
        _LOGGER.debug(f'Added buttons: {switches}')


class ZontSwitchBase(CoordinatorEntity, SwitchEntity):

    def __init__(self, coordinator: ZontCoordinator) -> None:
        super().__init__(coordinator)
        self._coord: ZontCoordinator = coordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._coord.zont_ws_api.is_connected:
            return False
        return True


class SwitchZont(ZontSwitchBase):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._control_id = control_state.get(WS_KEY_ID)
        self._name = control_state.get(WS_KEY_NAME)
        self._unique_id = unique_id
        self._attr_device_info = coordinator.get_devices_info()

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        if not self.hass:
            return f"<Button entity {self.name}>"
        return super().__repr__()

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        control_state = self._coord.data.get(self._control_id)
        if control_state:
            return control_state.get(WS_KEY_STATE)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._coord.zont_ws_api.send_command(
            self._control_id, COMMAND_ON
        )

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._coord.zont_ws_api.send_command(
            self._control_id, COMMAND_OFF
        )

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
