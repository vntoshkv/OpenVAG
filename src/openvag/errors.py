"""Errors exposed by the diagnostic core."""

from typing import Optional


class DiagnosticError(Exception):
    """Base class for a normalized diagnostic failure."""


class AdapterUnavailableError(DiagnosticError):
    """The selected adapter or its transport is unavailable."""


class ConnectionFailedError(DiagnosticError):
    """The adapter did not complete initialization."""


class TransportTimeoutError(DiagnosticError):
    """The adapter did not provide a response before the timeout."""


class ProtocolNegativeResponseError(DiagnosticError):
    """The ECU returned a negative response (service 0x7F).

    ``nrc`` is the negative response code when it can be decoded; it remains
    ``None`` when the response is too short rather than guessed.
    """

    def __init__(self, message: str, nrc: Optional[int] = None) -> None:
        super().__init__(message)
        self.nrc = nrc


class MalformedResponseError(DiagnosticError):
    """A response could not be parsed as an expected OBD-II response."""


class ServiceUnsupportedError(DiagnosticError):
    """The adapter reported NO DATA: no ECU answered that request."""
