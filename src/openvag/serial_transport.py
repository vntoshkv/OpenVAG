"""Serial line transport for ELM327 Bluetooth classic and USB adapters.

Bluetooth classic ELM327 modules normally appear as an OS serial device after
pairing (on macOS, usually ``/dev/cu.*``). pySerial is an optional extra:
``pip install -e '.[serial]'``. The core package and its test suite do not
require it; tests inject a fake serial device.
"""

import re
import time
from typing import List, Optional

from .errors import AdapterUnavailableError, TransportTimeoutError
from .transport import LineTransport


def _pyserial_factory(port: str, baudrate: int):
    try:
        import serial
    except ImportError as error:
        raise AdapterUnavailableError(
            "pyserial is required for --serial; install with: pip install -e '.[serial]'"
        ) from error
    try:
        return serial.Serial(port=port, baudrate=baudrate, timeout=0.1)
    except (OSError, ValueError) as error:
        raise AdapterUnavailableError("cannot open serial port {}: {}".format(port, error)) from error


def list_serial_ports() -> List[str]:
    """Return OS serial device names, or raise if pySerial is not installed."""
    try:
        from serial.tools import list_ports
    except ImportError as error:
        raise AdapterUnavailableError(
            "pyserial is required for serial support; install with: python -m pip install -e '.[serial]'"
        ) from error
    return sorted(port.device for port in list_ports.comports())


class SerialLineTransport(LineTransport):
    """A serial transport for ELM327 Bluetooth/USB adapters.

    ``serial_factory`` is injectable for tests. The default factory opens the
    port through pySerial with the requested baud rate.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 38400,
        serial_factory=None,
        max_response_bytes: int = 65536,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._serial_factory = serial_factory
        self._device = None
        self._max_response_bytes = max_response_bytes

    @property
    def endpoint(self) -> str:
        return "{}@{} baud".format(self._port, self._baudrate)

    def connect(self) -> None:
        if self._device is not None:
            return
        factory = self._serial_factory or _pyserial_factory
        device = factory(self._port, self._baudrate)
        self._device = device
        reset = getattr(device, "reset_input_buffer", None)
        if reset is not None:
            try:
                reset()
            except OSError:
                pass

    def request(self, command: str, timeout_seconds: float) -> List[str]:
        self.connect()
        assert self._device is not None
        device = self._device
        try:
            device.write((command + "\r").encode("ascii"))
            flush = getattr(device, "flush", None)
            if flush is not None:
                flush()
        except OSError as error:
            self._abort()
            raise AdapterUnavailableError(
                "failed to write {} to {}: {}".format(command, self.endpoint, error)
            ) from error

        buffer = bytearray()
        deadline = time.monotonic() + timeout_seconds
        while True:
            prompt_index = buffer.find(b">")
            if prompt_index >= 0:
                payload = bytes(buffer[:prompt_index])
                if payload.strip():
                    return self._decode_lines(payload)
                del buffer[:prompt_index + 1]
                continue

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._abort()
                raise TransportTimeoutError(
                    "timeout waiting for response to {} from {}".format(command, self.endpoint)
                )
            try:
                device.timeout = max(0.01, min(remaining, 0.2))
            except (AttributeError, ValueError):
                pass
            try:
                chunk = device.read(64)
            except OSError as error:
                self._abort()
                raise AdapterUnavailableError(
                    "serial read failed while waiting for {}: {}".format(command, error)
                ) from error
            if not chunk:
                continue
            if isinstance(chunk, str):
                chunk = chunk.encode("ascii", errors="replace")
            buffer.extend(chunk)
            if len(buffer) > self._max_response_bytes:
                self._abort()
                raise AdapterUnavailableError(
                    "response to {} exceeded {} bytes".format(command, self._max_response_bytes)
                )

    def close(self) -> None:
        self._abort()

    def _abort(self) -> None:
        device, self._device = self._device, None
        if device is not None:
            try:
                device.close()
            except OSError:
                pass

    @staticmethod
    def _decode_lines(payload: bytes) -> List[str]:
        text = payload.decode("ascii", errors="replace")
        parts = re.split(r"[\r\n]+", text)
        return [part.strip() for part in parts if part.strip()]
