import json
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)
from .const import (
    DOMAIN, PLATFORMS, MANUFACTURER, ENTRIES, TIME_UPDATE, CONFIGURATION_URL,
    CURRENT_ENTITY_IDS,
)
from .core.zont_data import ZontData

from .core.zont_ws_api import ZontWsApi


_LOGGER = logging.getLogger(__name__)


# def remove_entity(hass: HomeAssistant, current_entries_id: list,
#                   config_entry: ConfigEntry):
#     """Удаление неиспользуемых сущностей"""
#     entity_registry = async_get(hass)
#     remove_entities = []
#     for entity_id, entity in entity_registry.entities.items():
#         if entity.config_entry_id == config_entry.entry_id:
#             if entity.unique_id not in current_entries_id:
#                 remove_entities.append(entity_id)
#     for entity_id in remove_entities:
#         entity_registry.async_remove(entity_id)
#         _LOGGER.info(f'Outdated entity deleted {entity_id}')


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug('async_setup_entry start')
    # config_entry.async_on_unload(
    #     config_entry.add_update_listener(update_listener)
    # )
    entry_id = config_entry.entry_id
    name = config_entry.data.get('name')
    url = config_entry.data.get('url')
    login = config_entry.data.get('login')
    password = config_entry.data.get('password')
    zont_ws_api = ZontWsApi(hass, name, url, login, password)

    coordinator = ZontCoordinator(hass, zont_ws_api)

    await coordinator.init_device()
    await coordinator.async_config_entry_first_refresh()

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
    # remove_entity(hass, current_entries_id, config_entry)
    _LOGGER.debug(f'The unique ID of the current device entities {name}:'
                  f' {current_entries_id}')
    _LOGGER.debug(f'Number of relevant entities: '
                  f'{len(current_entries_id)}')
    return True


# async def update_listener(hass, entry):
#     """Вызывается при изменении настроек интеграции."""
#     _LOGGER.info(f'Restarting integration for entry_id: {entry.entry_id})')
#     await hass.config_entries.async_reload(entry.entry_id)
#
# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Unload a config entry."""
#     _LOGGER.info(f'Unloading the zont_ha integration: {entry.entry_id}')
#     try:
#         unload_ok = await hass.config_entries.async_unload_platforms(
#             entry, PLATFORMS
#         )
#         hass.data[DOMAIN][ENTRIES].pop(entry.entry_id)
#
#         return unload_ok
#     except Exception as e:
#         _LOGGER.error(f'Error uploading the integration: {e}')
#         return False


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
        self.zont_data: ZontData = ZontData()

    def get_devices_info(self):
        device_info = DeviceInfo(**{
            "identifiers": {(DOMAIN, self.zont_ws_api.name)},
            "name": self.zont_ws_api.name,
            "sw_version":self.zont_data.device_info.software,
            "hw_version": self.zont_data.device_info.hardware,
            "configuration_url": CONFIGURATION_URL,
            "model": self.zont_data.device_info.model,
            "manufacturer": MANUFACTURER,
        })
        return device_info

    async def update_device_info(self):
        text = await self.zont_ws_api.send_system_command('#S7?')
        _LOGGER.debug(f'updated device info: {text}')
        if text:
            (self.zont_data.device_info.model,
             self.zont_data.device_info.software,
             self.zont_data.device_info.hardware) = text.split(':')[1].split(' ')

    async def update_ids(self):
        ids = await self.zont_ws_api.get_ids()
        actual_ids = []
        _LOGGER.debug(f'All updated ids: {ids}. Count: {len(ids)}')
        for id in ids:
            state_control = await self.zont_ws_api.get_state(id)
            if not 'failed' in state_control:
                actual_ids.append(id)
        _LOGGER.debug(f'Actual ids: {actual_ids}. Count: {len(actual_ids)}')
        self.zont_data.ids = actual_ids

    async def init_device(self):
        _LOGGER.debug(f'Controller is initializing... '
                      f'(name: {self.zont_ws_api.name})')
        try:
            await self.update_device_info()
            await self.update_ids()
            _LOGGER.debug(f'Controller is initializing... '
                          f'(name: {self.zont_ws_api.name})')
        except Exception as err:
            _LOGGER.error(f'Initializing failed.'
                          f'(name: {self.zont_ws_api.name}). error: {err}')

    async def _async_update_data(self):
        """Обновление данных API zont"""
        _LOGGER.warning(f'Start update data.')
        for id in self.zont_data.ids:
            state_control = await self.zont_ws_api.get_state(id)
            self.zont_data.controls.update({id: state_control})
        _LOGGER.warning(f'Finish update data.')
        _LOGGER.debug(f'data: {self.zont_data.controls}')
