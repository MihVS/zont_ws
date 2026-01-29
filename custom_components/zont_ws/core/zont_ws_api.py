import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from ..const import (
    WS_TIMEOUT_REQUEST, HEARTBEAT, WS_KEY_USER, WS_KEY_AUTH,
    WS_KEY_REQUEST_IDS, WS_KEY_IDS, WS_KEY_ID, WS_KEY_REQUEST_STATE,
    WS_KEY_CMD, WS_KEY_SERVICE_CMD, WS_KEY_SERVICE_CMD_RESULT, WS_KEY_PASS,
    WS_KEY_FAILED
)
from .exceptions import ZontAuthError, ZontWsError, ZontUrlError, ZontInitError

_LOGGER = logging.getLogger(__name__)


class ZontWsApi:
    def __init__(self,
            hass: HomeAssistant,
            name: str,
            url: str,
            login: str,
            password: str) -> None:
        self._hass = hass
        self.name = name
        self.url = url
        self._host = self.get_ip(url)
        self._login = login
        self._password = password
        self._session = async_get_clientsession(hass)
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._lock = asyncio.Lock()
        self._connected = False
        self._listener_task = None
        self._callbacks = []

    @staticmethod
    def get_ip(url: str) -> str:
        try:
            ip = url.split('/')[2]
        except Exception as err:
            _LOGGER.error(f'The URL is incorrect.')
            raise ZontUrlError
        return ip

    async def connect(self) -> None:
        """Open websocket and authorize."""
        if self._connected:
            return

        _LOGGER.debug(f'Connecting to ZONT WS: {self._host}')

        try:
            self._ws = await self._session.ws_connect(
                url= self.url,
                ssl=False,
                heartbeat=HEARTBEAT,
                timeout=WS_TIMEOUT_REQUEST,
            )

            await self._ws.send_json(
                {
                    WS_KEY_USER: self._login,
                    WS_KEY_PASS: self._password,
                }
            )

            msg = await self._ws.receive(timeout=5)

            if msg.type != aiohttp.WSMsgType.TEXT:
                raise ZontWsError(f'Invalid auth response. Host: {self._host}')

            data = msg.json()
            _LOGGER.debug(f'message from host: {self._host} -> {data}')
            if data.get(WS_KEY_AUTH) != 200:
                raise ZontAuthError(f'ZONT authentication failed! '
                                    f'Host: {self._host}')

            self._connected = True
            _LOGGER.debug(f'ZONT WS connected and authorized. '
                          f'Host: {self._host}')

        except Exception as err:
            await self.close()
            raise ZontWsError(f'WS connect failed: {err}. '
                              f'Host: {self._host}') from err

    async def create_listener_task(self):
        _LOGGER.debug(f'Creating listener task...')
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self):
        _LOGGER.debug('WS listener started')
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    for cb in self._callbacks:
                        cb(data)

                elif msg.type in (
                    aiohttp.WSMsgType.ERROR,
                    aiohttp.WSMsgType.CLOSED,
                ):
                    break

        except Exception as err:
            _LOGGER.error(f'WS listen error: {err}')

        finally:
            _LOGGER.warning('WS listener stopped')
            self._connected = False

    def add_listener(self, callback):
        self._callbacks.append(callback)

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self._ws:
            _LOGGER.debug(f'Closing ZONT WS. Host: {self._host}')
            await self._ws.close()
        self._connected = False
        _LOGGER.debug(f'WS closed. Host: {self._host}')
        self._ws = None
        self._connected = False

    async def send_message(self, payload: dict[str, Any]):
        async with self._lock:
            if not self._connected:
                _LOGGER.error(f'WS not connected. Host: {self._host}')
                raise ZontWsError('WS not connected')
            _LOGGER.debug(f'Host: {self._host}. ZONT WS → {payload}')
            await self._ws.send_json(payload)

    async def get_init_data(self) -> dict:
        data = {}

        await self.get_ids()
        deadline = asyncio.get_running_loop().time() + 3
        while asyncio.get_running_loop().time() < deadline:
            try:
                msg = await self._ws.receive(timeout=1)
            except asyncio.TimeoutError:
                continue
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue
            control_data = msg.json()
            _LOGGER.debug(f'ZONT WS ← {control_data}')
            if WS_KEY_IDS in control_data:
                _LOGGER.debug(f'Got ids for initialization.')
                data.update(control_data)
        if not data.get(WS_KEY_IDS):
            _LOGGER.error(f'Host: {self._host}. Init failed.')
            raise ZontInitError('Could not get ids.')

        await self.send_system_command()
        for control_id in data[WS_KEY_IDS]:
            await self.get_state(control_id)

        deadline = asyncio.get_running_loop().time() + 10

        while asyncio.get_running_loop().time() < deadline:
            try:
                msg = await self._ws.receive(timeout=1)
            except asyncio.TimeoutError:
                continue
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue
            control_data = msg.json()
            if WS_KEY_FAILED in control_data:
                continue
            if WS_KEY_ID in control_data:
                data.update({control_data[WS_KEY_ID]: control_data})
                _LOGGER.debug(f'Init data updated by '
                              f'"{control_data[WS_KEY_ID]}: {control_data}"')
            else:
                data.update(control_data)
                _LOGGER.debug(f'Init data updated by {control_data}')
        return data

    async def get_ids(self, obj_type: str = 255):
        """Request list of object IDs."""
        await self.send_message({WS_KEY_REQUEST_IDS: obj_type})

    async def get_state(self, obj_id: int):
        """Request object state."""
        _LOGGER.debug(f'Host: {self._host}. Get state for id: {obj_id}')
        await self.send_message({WS_KEY_ID: obj_id, WS_KEY_REQUEST_STATE: 0,})

    async def send_command(self, obj_id: int, cmd: int) -> dict[str, Any]:
        """Send command to object."""
        return await self.send_message({WS_KEY_ID: obj_id, WS_KEY_CMD: cmd,})

    async def send_system_command(self):
        """Send system command (#S7?)."""
        await self.send_message({WS_KEY_SERVICE_CMD: '#S7?'})
