class ZontWsError(Exception):
    """Base ZONT WS error."""


class ZontAuthError(ZontWsError):
    """Authentication failed."""


class ZontUrlError(ZontWsError):
    """URL failed."""
