"""Errors exposed by the diagnostic core."""


class DiagnosticError(Exception):
    """Base class for a normalized diagnostic failure."""


class AdapterUnavailableError(DiagnosticError):
    """The selected adapter or its transport is unavailable."""


class ConnectionFailedError(DiagnosticError):
    """The adapter did not complete initialization."""


class TransportTimeoutError(DiagnosticError):
    """The adapter did not provide a response before the timeout."""


class MalformedResponseError(DiagnosticError):
    """A response could not be parsed as an expected OBD-II response."""


class ServiceUnsupportedError(DiagnosticError):
    """The ECU explicitly rejected an OBD-II service."""
