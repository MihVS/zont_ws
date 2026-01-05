import asyncio
import logging
from typing import Any

import aiohttp

from ..const import (
    WS_TIMEOUT_REQUEST, HEARTBEAT, WS_KEY_USER, WS_KEY_AUTH,
    WS_KEY_REQUEST_IDS, WS_KEY_IDS, WS_KEY_ID, WS_KEY_REQUEST_STATE,
    WS_KEY_CMD, WS_KEY_SERVICE_CMD, WS_KEY_SERVICE_CMD_RESULT
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class ZontWsError(Exception):
    """Base ZONT WS error."""


class ZontAuthError(ZontWsError):
    """Authentication failed."""


class ZontWsApi:
    def __init__(self, hass, host: str, user: str, password: str) -> None:
        self._hass = hass
        self._host = host
        self._user = user
        self._password = password

        self._session = async_get_clientsession(hass)
        self._ws: aiohttp.ClientWebSocketResponse | None = None

        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> None:
        """Open websocket and authorize."""
        if self._connected:
            return

        _LOGGER.debug(f'Connecting to ZONT WS: {self._host}')

        try:
            self._ws = await self._session.ws_connect(
                url= self._host,
                heartbeat=HEARTBEAT,
                timeout=WS_TIMEOUT_REQUEST,
            )

            await self._ws.send_json(
                {
                    WS_KEY_USER: self._user,
                    WS_KEY_AUTH: self._password,
                }
            )

            msg = await self._ws.receive(timeout=10)

            if msg.type != aiohttp.WSMsgType.TEXT:
                raise ZontWsError(f'Invalid auth response. Host: {self._host}')

            data = msg.json()
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

    async def close(self) -> None:
        """Close websocket."""
        if self._ws is not None:
            _LOGGER.debug(f'Closing ZONT WS. Host: {self._host}')
            try:
                await self._ws.close()
            except Exception:
                pass

        self._ws = None
        self._connected = False

    async def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send request and wait for response."""
        async with self._lock:
            if not self._connected:
                await self.connect()

            try:
                _LOGGER.debug(f'ZONT WS → {payload}')
                await self._ws.send_json(payload)

                msg = await self._ws.receive(timeout=15)

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    _LOGGER.debug(f'ZONT WS ← {data}')
                    return data

                if msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.ERROR,
                ):
                    raise ZontWsError(f'WebSocket closed. Host: {self._host}')

                raise ZontWsError(f'Unexpected WS msg: {msg.type}. '
                                  f'Host: {self._host}')

            except Exception as err:
                _LOGGER.warning(f'ZONT WS error (host: {self._host}), '
                                f'reconnect needed: {err}')
                await self.close()
                raise

    async def get_ids(self, obj_type: int = 255) -> list[int]:
        """Request list of object IDs."""
        data = await self.request({WS_KEY_REQUEST_IDS: obj_type})
        return data.get(WS_KEY_IDS, [])

    async def get_state(self, obj_id: int) -> dict[str, Any]:
        """Request object state."""
        return await self.request(
            {
                WS_KEY_ID: obj_id,
                WS_KEY_REQUEST_STATE: 0,
            }
        )

    async def send_command(self, obj_id: int, cmd: Any) -> dict[str, Any]:
        """Send command to object."""
        return await self.request(
            {
                WS_KEY_ID: obj_id,
                WS_KEY_CMD: cmd,
            }
        )

    async def send_system_command(self, scmd: str) -> str:
        """Send system command (#S7?, etc)."""
        data = await self.request({WS_KEY_SERVICE_CMD: scmd})
        return data.get(WS_KEY_SERVICE_CMD_RESULT, '')
