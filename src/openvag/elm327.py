"""Read-only ELM327 command handling.

No serial implementation is included yet: an application supplies a LineTransport.
This keeps unverified hardware details outside the protocol core.
"""

from dataclasses import dataclass
from typing import Dict, List

from .errors import ConnectionFailedError, MalformedResponseError, ServiceUnsupportedError, TransportTimeoutError
from .transport import LineTransport


@dataclass(frozen=True)
class AdapterCapabilities:
    """Reported adapter identification and initialization replies."""

    version: str
    initialization: Dict[str, str]


class Elm327Adapter:
    """A deliberately read-only subset of the ELM327 interface."""

    _INITIALIZATION_COMMANDS = ("ATZ", "ATE0", "ATL0", "ATS0", "ATH0", "ATSP0")

    def __init__(self, transport: LineTransport, timeout_seconds: float = 2.0) -> None:
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._connected = False

    def connect(self) -> AdapterCapabilities:
        replies: Dict[str, str] = {}
        for command in self._INITIALIZATION_COMMANDS:
            response = self._exchange(command)
            if self._is_error(response):
                raise ConnectionFailedError("ELM327 rejected {}: {}".format(command, response))
            replies[command] = response
        version = replies["ATZ"]
        if not version:
            raise ConnectionFailedError("ELM327 did not report a version for ATZ")
        self._connected = True
        return AdapterCapabilities(version=version, initialization=replies)

    def request_obd(self, request: str) -> List[int]:
        """Send an explicitly supplied read-only standard OBD-II request."""
        if not self._connected:
            raise ConnectionFailedError("adapter is not connected")
        normalized = request.upper().replace(" ", "")
        if normalized not in {"0100", "010C", "010D", "03"}:
            raise ValueError("request is not in the read-only prototype allowlist: {}".format(request))
        response = self._exchange(normalized)
        if response == "NO DATA" or response.startswith("7F"):
            raise ServiceUnsupportedError("ECU did not support {}: {}".format(normalized, response))
        return self._parse_hex_bytes(response)

    def close(self) -> None:
        self._connected = False
        self._transport.close()

    def _exchange(self, command: str) -> str:
        try:
            response = self._transport.request(command, self._timeout_seconds)
        except TimeoutError as error:
            raise TransportTimeoutError("timeout waiting for {}".format(command)) from error
        return " ".join(response.strip().upper().split())

    @staticmethod
    def _is_error(response: str) -> bool:
        return response in {"?", "ERROR", "STOPPED", "UNABLE TO CONNECT"}

    @staticmethod
    def _parse_hex_bytes(response: str) -> List[int]:
        compact = response.replace(" ", "")
        if len(compact) == 0 or len(compact) % 2 or any(char not in "0123456789ABCDEF" for char in compact):
            raise MalformedResponseError("not a hexadecimal OBD-II response: {!r}".format(response))
        return [int(compact[index:index + 2], 16) for index in range(0, len(compact), 2)]
