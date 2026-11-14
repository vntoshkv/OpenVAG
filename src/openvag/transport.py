"""Small, injectable line-oriented transport boundary for ELM-compatible adapters."""

from abc import ABC, abstractmethod
from typing import List


class LineTransport(ABC):
    """A transport that exchanges one ELM command and its textual response.

    Implementations return the response as logical lines, without the ELM
    prompt (``>``). They may include the command echo and adapter status lines
    such as ``SEARCHING...`` or ``BUS INIT: OK``; ``Elm327Adapter`` removes
    those before interpreting data. Keeping the raw lines here preserves the
    boundary between multiple ECU responses, which must not be concatenated.
    """

    @abstractmethod
    def request(self, command: str, timeout_seconds: float) -> List[str]:
        """Send *command* and return its response lines without the ELM prompt."""

    @abstractmethod
    def close(self) -> None:
        """Release the transport resource. Calling it twice must be safe."""
