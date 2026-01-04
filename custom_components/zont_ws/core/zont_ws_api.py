import asyncio
import logging
from typing import Any

import aiohttp
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

        _LOGGER.debug("Connecting to ZONT WS: %s", self._host)

        try:
            self._ws = await self._session.ws_connect(
                url= self._host,
                heartbeat=30,
                timeout=10,
            )

            await self._ws.send_json(
                {
                    "user": self._user,
                    "pass": self._password,
                }
            )

            msg = await self._ws.receive(timeout=10)

            if msg.type != aiohttp.WSMsgType.TEXT:
                raise ZontWsError("Invalid auth response")

            data = msg.json()
            if data.get("auth") != 200:
                raise ZontAuthError("ZONT authentication failed")

            self._connected = True
            _LOGGER.debug("ZONT WS connected and authorized")

        except Exception as err:
            await self.close()
            raise ZontWsError(f"WS connect failed: {err}") from err

    async def close(self) -> None:
        """Close websocket."""
        if self._ws is not None:
            _LOGGER.debug("Closing ZONT WS")
            try:
                await self._ws.close()
            except Exception:
                pass

        self._ws = None
        self._connected = False

    async def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send request and wait for response.
        Ensures:
        - single request at a time
        - reconnect on failure
        """
        async with self._lock:
            if not self._connected:
                await self.connect()

            try:
                _LOGGER.debug("ZONT WS → %s", payload)
                await self._ws.send_json(payload)

                msg = await self._ws.receive(timeout=15)

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    _LOGGER.debug("ZONT WS ← %s", data)
                    return data

                if msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.ERROR,
                ):
                    raise ZontWsError("WebSocket closed")

                raise ZontWsError(f"Unexpected WS msg: {msg.type}")

            except Exception as err:
                _LOGGER.warning("ZONT WS error, reconnect needed: %s", err)
                await self.close()
                raise

    async def get_ids(self, obj_type: int = 255) -> list[int]:
        """Request list of object IDs."""
        data = await self.request({"req_ids": obj_type})
        return data.get("ids", [])

    async def get_state(self, obj_id: int) -> dict[str, Any]:
        """Request object state."""
        return await self.request(
            {
                "id": obj_id,
                "req_state": 0,
            }
        )

    async def send_command(self, obj_id: int, cmd: Any) -> dict[str, Any]:
        """Send command to object."""
        return await self.request(
            {
                "id": obj_id,
                "cmd": cmd,
            }
        )

    async def send_system_command(self, scmd: str) -> str:
        """Send system command (#S7?, etc)."""
        data = await self.request({"scmd": scmd})
        return data.get("scmdres", "")
