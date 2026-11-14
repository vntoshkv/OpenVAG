"""Decoders for standard, read-only OBD-II data used by the prototype.

Only identifiers and formulas that are part of the public OBD-II/SAE J1979
service set are included. Each request is capability-gated by the vehicle's
supported-PID bitmap before it is sent. Unknown or unsupported values are not
guessed.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

from .errors import MalformedResponseError


@dataclass(frozen=True)
class Measurement:
    name: str
    value: float
    unit: str
    request: str


@dataclass(frozen=True)
class MonitorStatus:
    """The two unambiguously defined parts of PID 01.

    The remaining readiness bytes are preserved for later, source-reviewed
    decoding rather than interpreted here.
    """

    mil_on: bool
    dtc_count: int
    readiness_bytes: Tuple[int, int, int]
    request: str


def _require_prefix(values: List[int], prefix: List[int], length: int) -> None:
    if len(values) < length or values[:len(prefix)] != prefix:
        raise MalformedResponseError("unexpected OBD-II response bytes: {}".format(values))


def _payload(response: Iterable[int], pid: int, length: int) -> List[int]:
    values = list(response)
    _require_prefix(values, [0x41, pid], 2 + length)
    return values[2:2 + length]


def _measurement(
    pid: int,
    name: str,
    unit: str,
    length: int,
    formula: Callable[[List[int]], float],
) -> Callable[[Iterable[int]], Measurement]:
    def decode(response: Iterable[int]) -> Measurement:
        values = _payload(response, pid, length)
        return Measurement(name, float(formula(values)), unit, "01{:02X}".format(pid))

    return decode


def decode_monitor_status(response: Iterable[int]) -> MonitorStatus:
    values = _payload(response, 0x01, 4)
    status = values[0]
    return MonitorStatus(
        mil_on=bool(status & 0x80),
        dtc_count=status & 0x7F,
        readiness_bytes=(values[1], values[2], values[3]),
        request="0101",
    )


def decode_engine_rpm(response: Iterable[int]) -> Measurement:
    return _measurement(
        0x0C, "engine_rpm", "rpm", 2, lambda v: (v[0] * 256 + v[1]) / 4.0
    )(response)


def decode_vehicle_speed(response: Iterable[int]) -> Measurement:
    return _measurement(0x0D, "vehicle_speed", "km/h", 1, lambda v: v[0])(response)


def decode_supported_pids(response: Iterable[int], base_pid: int = 0x00) -> List[int]:
    """Decode one 32-PID availability bitmap (0100, 0120, or 0140).

    The base PID must match the response: 0x00 for 0100, 0x20 for 0120,
    0x40 for 0140. This reports only standard PIDs; it says nothing about
    vendor-specific services or the semantic meaning of a value.
    """
    values = list(response)
    _require_prefix(values, [0x41, base_pid], 6)
    supported = []
    for byte_offset, byte_value in enumerate(values[2:6]):
        for bit in range(8):
            if byte_value & (1 << (7 - bit)):
                supported.append(base_pid + (byte_offset * 8) + bit + 1)
    return supported


def decode_dtc_response(response: Iterable[int]) -> List[str]:
    return _decode_dtc(response, 0x43)


def decode_pending_dtc_response(response: Iterable[int]) -> List[str]:
    return _decode_dtc(response, 0x47)


def decode_permanent_dtc_response(response: Iterable[int]) -> List[str]:
    return _decode_dtc(response, 0x4A)


def _decode_dtc(response: Iterable[int], response_code: int) -> List[str]:
    values = list(response)
    _require_prefix(values, [response_code], 1)
    payload = values[1:]
    if len(payload) % 2:
        raise MalformedResponseError("DTC payload has an odd number of bytes")
    return [_decode_dtc_code(first, second) for first, second in zip(payload[::2], payload[1::2]) if first or second]


def _decode_dtc_code(first: int, second: int) -> str:
    family = "PCBU"[(first >> 6) & 0x03]
    return "{}{:X}{:X}{:02X}".format(family, (first >> 4) & 0x03, first & 0x0F, second)


# Ordered list of live-data PIDs collected by the standard snapshot. Only
# entries advertised in the vehicle's supported-PID bitmap are requested.
LIVE_PID_ORDER: Tuple[int, ...] = (
    0x01,  # monitor status
    0x04,  # calculated engine load
    0x05,  # coolant temperature
    0x06,  # short-term fuel trim, bank 1
    0x07,  # long-term fuel trim, bank 1
    0x08,  # short-term fuel trim, bank 2 (if supported)
    0x09,  # long-term fuel trim, bank 2 (if supported)
    0x0A,  # fuel pressure
    0x0B,  # intake manifold pressure
    0x0C,  # engine RPM
    0x0D,  # vehicle speed
    0x0E,  # timing advance
    0x0F,  # intake air temperature
    0x10,  # mass air flow
    0x11,  # throttle position
    0x1F,  # run time since engine start
    0x21,  # distance travelled with MIL on
    0x2F,  # fuel tank level
    0x31,  # distance since codes cleared
    0x33,  # barometric pressure
    0x42,  # control module voltage
    0x46,  # ambient air temperature
    0x5C,  # engine oil temperature
    0x5E,  # engine fuel rate
)

PID_DECODERS: Dict[int, Callable[[Iterable[int]], object]] = {
    0x01: decode_monitor_status,
    0x04: _measurement(0x04, "calculated_engine_load", "%", 1, lambda v: v[0] * 100.0 / 255.0),
    0x05: _measurement(0x05, "engine_coolant_temperature", "°C", 1, lambda v: v[0] - 40.0),
    0x06: _measurement(0x06, "short_term_fuel_trim_bank_1", "%", 1, lambda v: (v[0] - 128.0) * 100.0 / 128.0),
    0x07: _measurement(0x07, "long_term_fuel_trim_bank_1", "%", 1, lambda v: (v[0] - 128.0) * 100.0 / 128.0),
    0x08: _measurement(0x08, "short_term_fuel_trim_bank_2", "%", 1, lambda v: (v[0] - 128.0) * 100.0 / 128.0),
    0x09: _measurement(0x09, "long_term_fuel_trim_bank_2", "%", 1, lambda v: (v[0] - 128.0) * 100.0 / 128.0),
    0x0A: _measurement(0x0A, "fuel_pressure", "kPa", 1, lambda v: v[0] * 3.0),
    0x0B: _measurement(0x0B, "intake_manifold_pressure", "kPa", 1, lambda v: v[0]),
    0x0C: _measurement(0x0C, "engine_rpm", "rpm", 2, lambda v: (v[0] * 256 + v[1]) / 4.0),
    0x0D: _measurement(0x0D, "vehicle_speed", "km/h", 1, lambda v: v[0]),
    0x0E: _measurement(0x0E, "timing_advance", "°", 1, lambda v: v[0] / 2.0 - 64.0),
    0x0F: _measurement(0x0F, "intake_air_temperature", "°C", 1, lambda v: v[0] - 40.0),
    0x10: _measurement(0x10, "mass_air_flow", "g/s", 2, lambda v: (v[0] * 256 + v[1]) / 100.0),
    0x11: _measurement(0x11, "throttle_position", "%", 1, lambda v: v[0] * 100.0 / 255.0),
    0x1F: _measurement(0x1F, "run_time_since_engine_start", "s", 2, lambda v: v[0] * 256 + v[1]),
    0x21: _measurement(0x21, "distance_with_mil_on", "km", 2, lambda v: v[0] * 256 + v[1]),
    0x2F: _measurement(0x2F, "fuel_tank_level", "%", 1, lambda v: v[0] * 100.0 / 255.0),
    0x31: _measurement(0x31, "distance_since_codes_cleared", "km", 2, lambda v: v[0] * 256 + v[1]),
    0x33: _measurement(0x33, "barometric_pressure", "kPa", 1, lambda v: v[0]),
    0x42: _measurement(0x42, "control_module_voltage", "V", 2, lambda v: (v[0] * 256 + v[1]) / 1000.0),
    0x46: _measurement(0x46, "ambient_air_temperature", "°C", 1, lambda v: v[0] - 40.0),
    0x5C: _measurement(0x5C, "engine_oil_temperature", "°C", 1, lambda v: v[0] - 40.0),
    0x5E: _measurement(0x5E, "engine_fuel_rate", "L/h", 2, lambda v: (v[0] * 256 + v[1]) / 20.0),
}
