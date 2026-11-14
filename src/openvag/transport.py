"""Small, injectable line-oriented transport boundary for ELM-compatible adapters."""

from abc import ABC, abstractmethod


class LineTransport(ABC):
    """A transport that exchanges one ELM command and its textual response."""

    @abstractmethod
    def request(self, command: str, timeout_seconds: float) -> str:
        """Send *command* and return its response without the ELM prompt."""

    @abstractmethod
    def close(self) -> None:
        """Release the transport resource."""
