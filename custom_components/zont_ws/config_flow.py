import logging

import voluptuous as vol

from homeassistant import config_entries
from .const import (
    DOMAIN, LOGIN_DEFAULT, PASSWORD_DEFAULT, URL_DEFAULT
)
from .core.exceptions import ZontAuthError, ZontUrlError, ZontWsError
from .core.zont_ws_api import ZontWsApi

_LOGGER = logging.getLogger(__name__)


class ZontConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    data: dict = None

    async def async_step_user(self, user_input=None):
        _LOGGER.debug('async_step_user')
        errors: dict[str, str] = {}
        if user_input is not None:
            zont_ws: ZontWsApi | None = None
            try:
                _LOGGER.debug(f'Filled in fields: {user_input}')
                self.data = user_input
                name = user_input.get('name', '')
                url = user_input.get('url', '')
                login = user_input.get('login', '')
                password = user_input.get('password', '')
                zont_ws = ZontWsApi(self.hass, name, url, login, password)
                await zont_ws.connect()
                await zont_ws.close()
                return self.async_create_entry(title=name, data=self.data)
            except ZontAuthError:
                _LOGGER.error('Invalid login or password.')
                errors['base'] = 'invalid_auth'
            except ZontUrlError:
                _LOGGER.error('Invalid URL.')
                errors['base'] = 'invalid_url'
            except ZontWsError:
                _LOGGER.error(f'Cannot connect to ZONT ({url}).')
                errors['base'] = 'invalid_connect'
            except Exception as e:
                _LOGGER.error(f'Something went wrong, unknown error. {e}')
                errors['base'] = 'unknown'
            finally:
                if zont_ws is not None:
                    await zont_ws.close()
        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(
                {
                    vol.Required(schema='name', msg='name plc zont'): str,
                    vol.Required(schema='url', default=URL_DEFAULT): str,
                    vol.Required(schema='login', default=LOGIN_DEFAULT): str,
                    vol.Required(schema='password', default=PASSWORD_DEFAULT): str,
                }
            ),
            errors=errors
        )