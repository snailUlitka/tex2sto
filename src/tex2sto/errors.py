"""Application exceptions."""


class Tex2StoError(Exception):
    """Base class for expected user-facing failures."""


class SourceError(Tex2StoError):
    """The controlled source project is invalid."""


class ToolError(Tex2StoError):
    """An external document tool failed or is unavailable."""
