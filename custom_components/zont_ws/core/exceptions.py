from homeassistant.exceptions import HomeAssistantError


class ZontWsError(Exception):
    """Base ZONT WS error."""


class ZontAuthError(ZontWsError):
    """Authentication failed."""


class ZontInitError(ZontWsError):
    """Initialization failed."""


class ZontUrlError(ZontWsError):
    """URL failed."""


class TemperatureOutOfRangeError(HomeAssistantError):
    """The temperature is not set within the acceptable range."""


class SetPresetModeError(HomeAssistantError):
    """Error of set preset mode."""


class SetHvacModeError(HomeAssistantError):
    """Error of set HVAC mode."""
