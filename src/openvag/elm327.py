"""Read-only ELM327 command handling.

No hardware-specific transport is included here. The application supplies a
:class:`~openvag.transport.LineTransport`; Wi-Fi and Bluetooth implementations
live in their own modules. This keeps unverified adapter details outside the
protocol core.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .errors import (
    AdapterUnavailableError,
    ConnectionFailedError,
    DiagnosticError,
    MalformedResponseError,
    ProtocolNegativeResponseError,
    ServiceUnsupportedError,
    TransportTimeoutError,
)
from .transport import LineTransport


@dataclass(frozen=True)
class AdapterCapabilities:
    """Reported adapter identification and initialization replies."""

    version: str
    description: str
    protocol: str
    initialization: Dict[str, str]


@dataclass(frozen=True)
class ObdResponse:
    """One ECU response to an OBD-II request.

    A single request can produce several responses when more than one ECU
    answers. The index is an ordering hint only: with ELM headers disabled
    (``ATH0``) the adapter does not expose which ECU sent which line.
    """

    request: str
    values: Tuple[int, ...]
    response_index: int


class Elm327Adapter:
    """A deliberately read-only subset of the ELM327 interface."""

    _INITIALIZATION_COMMANDS = ("ATZ", "ATE0", "ATL0", "ATS0", "ATH0", "ATSP0")
    _IDENTIFICATION_COMMANDS = ("ATI", "AT@1", "ATDPN")
    _READ_ONLY_REQUESTS = frozenset({"0100", "010C", "010D", "03"})
    _RESET_TIMEOUT = 5.0
    _ADAPTER_ERRORS = frozenset(
        {
            "?",
            "ERROR",
            "STOPPED",
            "UNABLE TO CONNECT",
            "BUFFER FULL",
            "BUS BUSY",
            "CAN ERROR",
            "LV RESET",
            "FB ERROR",
            "DATA ERROR",
        }
    )
    _STATUS_PREFIXES = ("SEARCHING...", "SEARCHING", "BUS INIT: OK", "BUS INIT:", "BUS INIT")

    def __init__(
        self,
        transport: LineTransport,
        timeout_seconds: float = 2.0,
        obd_timeout_seconds: float = 15.0,
    ) -> None:
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._obd_timeout_seconds = obd_timeout_seconds
        self._connected = False
        self._capabilities: Optional[AdapterCapabilities] = None
        self._protocol = "unknown"

    @property
    def capabilities(self) -> Optional[AdapterCapabilities]:
        return self._capabilities

    @property
    def protocol(self) -> str:
        return self._protocol

    def connect(self) -> AdapterCapabilities:
        replies: Dict[str, str] = {}
        for command in self._INITIALIZATION_COMMANDS:
            try:
                lines = self._exchange(command, self._timeout_for(command))
            except AdapterUnavailableError as error:
                raise ConnectionFailedError(
                    "ELM327 initialization failed at {}: {}".format(command, error)
                ) from error
            if not lines or "NO DATA" in lines:
                raise ConnectionFailedError("ELM327 returned no response for {}".format(command))
            replies[command] = " ".join(lines)

        version = self._identify("ATI")
        if version == "unknown":
            version = replies.get("ATZ", "").strip() or "unknown"
        if version == "unknown":
            raise ConnectionFailedError("ELM327 did not report a version")

        description = self._identify("AT@1")
        protocol = self._identify("ATDPN")
        replies["ATI"] = version
        replies["AT@1"] = description
        replies["ATDPN"] = protocol

        self._protocol = protocol
        self._connected = True
        self._capabilities = AdapterCapabilities(version, description, protocol, replies)
        return self._capabilities

    def describe_protocol(self) -> str:
        """Ask the adapter which protocol it actually negotiated.

        Before the first OBD request an auto-selecting adapter usually reports
        an auto mode (for example ``A0``); afterwards it may report the concrete
        protocol (for example ``A6``). Failure leaves the previous value intact.
        """
        self._require_connected()
        try:
            lines = self._exchange("ATDPN", self._timeout_for("ATDPN"))
        except DiagnosticError:
            return self._protocol
        if lines and lines[0] not in {"NO DATA", "UNKNOWN"}:
            self._protocol = lines[0]
        return self._protocol

    def request_obd(self, request: str) -> List[ObdResponse]:
        """Send an explicitly supplied read-only standard OBD-II request."""
        self._require_connected()
        normalized = request.upper().replace(" ", "")
        if normalized not in self._READ_ONLY_REQUESTS:
            raise ValueError("request is not in the read-only prototype allowlist: {}".format(request))

        lines = self._exchange(normalized, self._obd_timeout_seconds)
        data_lines: List[str] = []
        for line in lines:
            cleaned = self._strip_obd_status(line)
            if not cleaned or cleaned == "NO DATA" or cleaned == "OK":
                continue
            if cleaned.startswith("7F"):
                raise self._negative_response(normalized, cleaned)
            if self._is_adapter_error(cleaned):
                raise AdapterUnavailableError("adapter error for {}: {}".format(normalized, cleaned))
            data_lines.append(cleaned)

        if not data_lines:
            raise ServiceUnsupportedError("ECU did not support {} (no data)".format(normalized))

        responses = []
        for index, line in enumerate(data_lines):
            responses.append(ObdResponse(normalized, tuple(self._parse_hex_bytes(line)), index))
        return responses

    def close(self) -> None:
        self._connected = False
        self._transport.close()

    def _require_connected(self) -> None:
        if not self._connected:
            raise ConnectionFailedError("adapter is not connected")

    def _timeout_for(self, command: str) -> float:
        if command == "ATZ":
            return self._RESET_TIMEOUT
        if command.startswith("AT"):
            return self._timeout_seconds
        return self._obd_timeout_seconds

    def _identify(self, command: str) -> str:
        try:
            lines = self._exchange(command, self._timeout_for(command))
        except DiagnosticError:
            return "unknown"
        if not lines or lines[0] in {"NO DATA", "UNKNOWN"}:
            return "unknown"
        return lines[0]

    def _exchange(self, command: str, timeout_seconds: float) -> List[str]:
        try:
            raw_lines = self._transport.request(command, timeout_seconds)
        except TimeoutError as error:
            raise TransportTimeoutError("timeout waiting for {}".format(command)) from error
        except OSError as error:
            raise AdapterUnavailableError("transport failure for {}: {}".format(command, error)) from error

        if isinstance(raw_lines, str):
            raw_lines = re.split(r"[\r\n]+", raw_lines)
        lines = self._normalize_lines(command, list(raw_lines))
        if not lines:
            raise AdapterUnavailableError("adapter returned no response for {}".format(command))
        for line in lines:
            if self._is_adapter_error(line):
                raise AdapterUnavailableError("adapter error for {}: {}".format(command, line))
        return lines

    @staticmethod
    def _normalize_lines(command: str, raw_lines: List[str]) -> List[str]:
        normalized = []
        command_upper = command.upper()
        for raw in raw_lines:
            text = " ".join(str(raw).strip().upper().split())
            text = text.split(">", 1)[0].strip()
            if not text:
                continue
            if text == command_upper:
                continue
            if text.startswith(command_upper + " "):
                text = text[len(command_upper) + 1:].strip()
                if not text:
                    continue
            normalized.append(text)
        return normalized

    def _strip_obd_status(self, line: str) -> str:
        text = line
        for prefix in self._STATUS_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        if text.startswith("OK "):
            text = text[3:].strip()
        if text in {"OK", "...OK"}:
            return ""
        return text

    @classmethod
    def _is_adapter_error(cls, line: str) -> bool:
        upper = line.upper()
        return upper in cls._ADAPTER_ERRORS or upper.startswith("UNABLE TO CONNECT")

    @staticmethod
    def _negative_response(request: str, line: str) -> ProtocolNegativeResponseError:
        values = Elm327Adapter._parse_hex_bytes(line)
        nrc = values[2] if len(values) >= 3 else None
        return ProtocolNegativeResponseError(
            "ECU returned a negative response to {}: {}".format(request, line),
            nrc=nrc,
        )

    @staticmethod
    def _parse_hex_bytes(response: str) -> List[int]:
        compact = response.replace(" ", "")
        if len(compact) == 0 or len(compact) % 2 or any(char not in "0123456789ABCDEF" for char in compact):
            raise MalformedResponseError("not a hexadecimal OBD-II response: {!r}".format(response))
        return [int(compact[index:index + 2], 16) for index in range(0, len(compact), 2)]
