import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import ZontCoordinator
from .const import (
    DOMAIN, CURRENT_ENTITY_IDS, ENTRIES, WS_KEY_ID, WS_KEY_TYPE, ZontType,
    WS_KEY_NAME, COMMAND_ON, HEATING_MODES, WS_KEY_STYPE, ZontWebElmType
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    entry_id = config_entry.entry_id

    coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]

    buttons = []
    for control_id, control_state in coordinator.data.items():
        if not isinstance(control_state, dict):
            continue
        type_control = control_state.get(WS_KEY_TYPE)
        match type_control:
            case ZontType.MODE:
                unique_id = f'{entry_id}{control_id}-button_mode'
                buttons.append(HeatingModeButton(
                    coordinator, control_state, unique_id)
                )
            case ZontType.WEB_ELEMENT:
                type_web_elm = control_state.get(WS_KEY_STYPE)
                if type_web_elm == ZontWebElmType.BUTTON:
                    unique_id = f'{entry_id}{control_id}-button_web_elm'
                    buttons.append(ButtonZont(
                        coordinator, control_state, unique_id)
                    )
    for button in buttons:
        hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id].append(
            button.unique_id)
    if buttons:
        async_add_entities(buttons)
        _LOGGER.debug(f'Added buttons: {buttons}')


class ZontButtonBase(CoordinatorEntity, ButtonEntity):

    def __init__(self, coordinator: ZontCoordinator) -> None:
        super().__init__(coordinator)
        self._coord: ZontCoordinator = coordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._coord.zont_ws_api.is_connected:
            return False
        return True


class ButtonZont(ZontButtonBase):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str
    ) -> None:
        super().__init__(coordinator)
        self._coord = coordinator
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

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._coord.zont_ws_api.send_command(
            self._control_id, COMMAND_ON
        )


class HeatingModeButton(ButtonZont):

    def __init__(self,
                 coordinator: ZontCoordinator,
                 control_state: dict,
                 unique_id: str
    ) -> None:
        super().__init__(coordinator, control_state, unique_id)
        self._attr_icon = self.get_icon(self._name)

    @staticmethod
    def get_icon(name_mode: str) -> str:
        for mode, icon in HEATING_MODES.items():
            if mode.lower() in name_mode.lower():
                return icon
        return 'mdi:refresh-circle'
