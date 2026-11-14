"""TCP line transport for ELM327 Wi-Fi bridges.

The adapter exposes a transparent TCP-to-UART bridge: commands are written with
a trailing carriage return and responses are read until the ELM prompt (``>``).
No platform-specific driver is needed.
"""

import re
import socket
import time
from typing import List, Optional

from .errors import AdapterUnavailableError, TransportTimeoutError
from .transport import LineTransport


class TcpLineTransport(LineTransport):
    """A TCP transport for ELM327-compatible Wi-Fi adapters."""

    def __init__(
        self,
        host: str,
        port: int = 35000,
        connect_timeout: float = 5.0,
        max_response_bytes: int = 65536,
    ) -> None:
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._max_response_bytes = max_response_bytes
        self._socket: Optional[socket.socket] = None

    @property
    def endpoint(self) -> str:
        return "{}:{}".format(self._host, self._port)

    def connect(self) -> None:
        if self._socket is not None:
            return
        try:
            self._socket = socket.create_connection(
                (self._host, self._port), timeout=self._connect_timeout
            )
        except OSError as error:
            raise AdapterUnavailableError(
                "cannot connect to {}: {}".format(self.endpoint, error)
            ) from error

    def request(self, command: str, timeout_seconds: float) -> List[str]:
        self.connect()
        assert self._socket is not None
        try:
            self._socket.settimeout(max(0.001, min(timeout_seconds, self._connect_timeout)))
            self._socket.sendall((command + "\r").encode("ascii"))
        except OSError as error:
            self._abort()
            raise AdapterUnavailableError(
                "failed to send {} to {}: {}".format(command, self.endpoint, error)
            ) from error

        buffer = bytearray()
        deadline = time.monotonic() + timeout_seconds
        while True:
            prompt_index = buffer.find(b">")
            if prompt_index >= 0:
                payload = bytes(buffer[:prompt_index])
                if payload.strip():
                    return self._decode_lines(payload)
                # Some Wi-Fi bridges send a greeting prompt as soon as the
                # socket opens. It is not a response to the command.
                del buffer[:prompt_index + 1]
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._abort()
                raise TransportTimeoutError(
                    "timeout waiting for response to {} from {}".format(command, self.endpoint)
                )
            self._socket.settimeout(max(0.001, remaining))
            try:
                chunk = self._socket.recv(4096)
            except socket.timeout as error:
                self._abort()
                raise TransportTimeoutError(
                    "timeout waiting for response to {} from {}".format(command, self.endpoint)
                ) from error
            except OSError as error:
                self._abort()
                raise AdapterUnavailableError(
                    "connection failure while waiting for {}: {}".format(command, error)
                ) from error
            if not chunk:
                self._abort()
                raise AdapterUnavailableError(
                    "connection closed before a response to {}".format(command)
                )
            buffer.extend(chunk)
            if len(buffer) > self._max_response_bytes:
                self._abort()
                raise AdapterUnavailableError(
                    "response to {} exceeded {} bytes".format(command, self._max_response_bytes)
                )

    def close(self) -> None:
        self._abort()

    def _abort(self) -> None:
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    @staticmethod
    def _decode_lines(payload: bytes) -> List[str]:
        text = payload.decode("ascii", errors="replace")
        parts = re.split(r"[\r\n]+", text)
        return [part.strip() for part in parts if part.strip()]
