"""Decoders for the small, standards-based OBD-II prototype subset."""

from dataclasses import dataclass
from typing import Iterable, List

from .errors import MalformedResponseError


@dataclass(frozen=True)
class Measurement:
    name: str
    value: float
    unit: str
    request: str


def decode_engine_rpm(response: Iterable[int]) -> Measurement:
    values = list(response)
    _require_prefix(values, [0x41, 0x0C], 4)
    return Measurement("engine_rpm", ((values[2] * 256) + values[3]) / 4.0, "rpm", "010C")


def decode_vehicle_speed(response: Iterable[int]) -> Measurement:
    values = list(response)
    _require_prefix(values, [0x41, 0x0D], 3)
    return Measurement("vehicle_speed", float(values[2]), "km/h", "010D")


def decode_supported_pids(response: Iterable[int]) -> List[int]:
    """Decode the standard mode 01, PID 00 availability bitmap.

    This reports only standard PID numbers advertised in the first 32-PID range;
    it does not establish that a particular vehicle implements any VAG-specific
    service or that a value is semantically verified for a vehicle.
    """
    values = list(response)
    _require_prefix(values, [0x41, 0x00], 6)
    supported = []
    for byte_offset, byte_value in enumerate(values[2:6]):
        for bit in range(8):
            if byte_value & (1 << (7 - bit)):
                supported.append((byte_offset * 8) + bit + 1)
    return supported


def decode_dtc_response(response: Iterable[int]) -> List[str]:
    values = list(response)
    _require_prefix(values, [0x43], 1)
    payload = values[1:]
    if len(payload) % 2:
        raise MalformedResponseError("DTC payload has an odd number of bytes")
    return [_decode_dtc(first, second) for first, second in zip(payload[::2], payload[1::2]) if first or second]


def _require_prefix(values: List[int], prefix: List[int], length: int) -> None:
    if len(values) < length or values[:len(prefix)] != prefix:
        raise MalformedResponseError("unexpected OBD-II response bytes: {}".format(values))


def _decode_dtc(first: int, second: int) -> str:
    family = "PCBU"[(first >> 6) & 0x03]
    return "{}{:X}{:X}{:02X}".format(family, (first >> 4) & 0x03, first & 0x0F, second)
