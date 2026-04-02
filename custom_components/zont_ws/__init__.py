import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)
from .const import (
    DOMAIN, PLATFORMS, MANUFACTURER, ENTRIES, TIME_UPDATE, CONFIGURATION_URL,
    CURRENT_ENTITY_IDS, WS_KEY_TYPE, ZontType, MODE_BOILER_NAMES, WS_KEY_NAME,
    WS_KEY_SERVICE_CMD_RESPONSE, WS_KEY_ID, WS_KEY_CMD_RESPONSE, WS_KEY_IDS,
)
from .core.exceptions import ZontInitError, ZontWsError
from .core.zont_data import ZontDeviceInfo
from .core.zont_ws_api import ZontWsApi

_LOGGER = logging.getLogger(__name__)


def remove_entity(hass: HomeAssistant, current_entries_id: list,
                  config_entry: ConfigEntry):
    """Удаление неиспользуемых сущностей"""
    entity_registry = async_get(hass)
    remove_entities = []
    for entity_id, entity in entity_registry.entities.items():
        if entity.config_entry_id == config_entry.entry_id:
            if entity.unique_id not in current_entries_id:
                remove_entities.append(entity_id)
    for entity_id in remove_entities:
        entity_registry.async_remove(entity_id)
        _LOGGER.info(f'Outdated entity deleted {entity_id}')


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug('async_setup_entry start')
    config_entry.async_on_unload(
        config_entry.add_update_listener(update_listener)
    )
    entry_id = config_entry.entry_id
    name = config_entry.data.get('name')
    url = config_entry.data.get('url')
    login = config_entry.data.get('login')
    password = config_entry.data.get('password')
    zont_ws_api = ZontWsApi(hass, name, url, login, password)

    coordinator = ZontCoordinator(hass, zont_ws_api)

    await coordinator.init_device()
    await coordinator.async_config_entry_first_refresh()
    coordinator.zont_ws_api.is_reconnecting = False

    _LOGGER.debug(f'config entry data: {config_entry.data}')

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(ENTRIES, {})
    hass.data[DOMAIN].setdefault(CURRENT_ENTITY_IDS, {})
    hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id] = []
    hass.data[DOMAIN][ENTRIES][entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        config_entry, PLATFORMS
    )
    current_entries_id = hass.data[DOMAIN][CURRENT_ENTITY_IDS][entry_id]
    remove_entity(hass, current_entries_id, config_entry)
    _LOGGER.debug(f'The unique ID of the current device entities {name}:'
                  f' {current_entries_id}')
    _LOGGER.debug(f'Number of relevant entities: '
                  f'{len(current_entries_id)}')
    return True


async def update_listener(hass, entry):
    """Вызывается при изменении настроек интеграции."""
    _LOGGER.info(f'Restarting integration for entry_id: {entry.entry_id})')
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    entry_id = entry.entry_id
    _LOGGER.info(f'Unloading the zont_ws integration: {entry_id}')
    try:
        coordinator: ZontCoordinator = hass.data[DOMAIN][ENTRIES][entry_id]
        coordinator.zont_ws_api.is_reconnecting = True
        await coordinator.zont_ws_api.close()
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        )
        hass.data[DOMAIN][ENTRIES].pop(entry_id)

        return unload_ok
    except Exception as e:
        _LOGGER.error(f'Error uploading the integration: {e}')
        return False


class ZontCoordinator(DataUpdateCoordinator):
    """Координатор для общего обновления данных"""

    _count_connect: int = 0

    def __init__(self, hass, zont_ws_api):
        super().__init__(
            hass,
            _LOGGER,
            name="ZONT Local",
            update_interval=timedelta(seconds=TIME_UPDATE),
        )
        self.zont_ws_api: ZontWsApi = zont_ws_api
        self.zont_info: ZontDeviceInfo = ZontDeviceInfo()
        self.ids_for_update = []
        self.data = {}

    async def _on_ws_message(self, data):
        _LOGGER.debug(f'{self.zont_ws_api.url}. ZONT Message <= {data}')
        if WS_KEY_CMD_RESPONSE in data:
            return
        if WS_KEY_ID in data:
            self.data.update({data[WS_KEY_ID]: data})
        else:
            self.data.update(data)
        self.async_set_updated_data(self.data)

    def get_devices_info(self):
        zont_info = self.data.get(WS_KEY_SERVICE_CMD_RESPONSE)
        if zont_info:
            (
                self.zont_info.model,
                self.zont_info.hardware,
                self.zont_info.software) = zont_info.split(':')[1].split(' ')

        device_info = DeviceInfo(**{
            "identifiers": {(DOMAIN, self.zont_ws_api.name)},
            "name": self.zont_ws_api.name,
            "sw_version": self.zont_info.software,
            "hw_version": self.zont_info.hardware,
            "configuration_url": CONFIGURATION_URL,
            "model": self.zont_info.model,
            "manufacturer": MANUFACTURER,
        })
        return device_info

    @staticmethod
    def check_mode(state_control: dict) -> bool:
        if state_control.get(WS_KEY_TYPE) == ZontType.MODE:
            for tag in MODE_BOILER_NAMES:
                name: str = state_control.get(WS_KEY_NAME)
                if not name:
                    return False
                if tag in name.lower():
                    return False
        return True

    async def init_device(self):
        _LOGGER.info(f'Controller is initializing... '
                      f'(name: {self.zont_ws_api.name})')
        try:
            await self.zont_ws_api.connect()
            self.data = await self.zont_ws_api.get_init_data()
            self.zont_ws_api.add_listener(self._on_ws_message)
            await self.zont_ws_api.start()
            _LOGGER.debug(f'Initialized data: {self.data}')
            _LOGGER.info(f'Controller initialized successfully. '
                          f'(name: {self.zont_ws_api.name})')
        except Exception as err:
            _LOGGER.error(f'Initializing failed.'
                          f'(name: {self.zont_ws_api.name}). error: {err}')
            raise ZontInitError

    async def _async_update_data(self):
        """Обновление данных API zont"""
        _LOGGER.info(f'Start polling the controller.')
        try:
            for control_id in self.ids_for_update:
                await self.zont_ws_api.get_state(control_id)
        except ZontWsError:
            _LOGGER.warning(f'Waiting connect to zont ({self.zont_ws_api.url})...')
        _LOGGER.info(f'Finish polling the controller.')
        return self.data
