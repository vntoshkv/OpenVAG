"""CLI entry point: simulator, Wi-Fi TCP, or Bluetooth/USB serial ELM327."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .elm327 import AdapterCapabilities, Elm327Adapter
from .errors import (
    AdapterUnavailableError,
    DiagnosticError,
    MalformedResponseError,
    ProtocolNegativeResponseError,
    ServiceUnsupportedError,
    TransportTimeoutError,
)
from .obd import (
    LIVE_PID_ORDER,
    PID_DECODERS,
    Measurement,
    MonitorStatus,
    decode_dtc_response,
    decode_pending_dtc_response,
    decode_permanent_dtc_response,
    decode_supported_pids,
)
from .serial_transport import SerialLineTransport, list_serial_ports
from .session import DiagnosticSession
from .simulator import SimulatedElm327Transport
from .tcp_transport import TcpLineTransport


def _status_for(error: DiagnosticError) -> str:
    if isinstance(error, ServiceUnsupportedError):
        return "unsupported"
    if isinstance(error, ProtocolNegativeResponseError):
        return "negative"
    if isinstance(error, MalformedResponseError):
        return "malformed"
    if isinstance(error, TransportTimeoutError):
        return "timeout"
    if isinstance(error, AdapterUnavailableError):
        return "unavailable"
    return "failed"


def _raw_hex(values) -> str:
    return " ".join("{:02X}".format(value) for value in values)


def _append_error(results, kind, request, error, response=None):
    entry = {
        "status": _status_for(error),
        "kind": kind,
        "request": request,
        "error": str(error),
    }
    if response is not None:
        entry["response_index"] = response.response_index
        entry["raw_hex"] = _raw_hex(response.values)
    results.append(entry)


def _append_decoded(results, kind, request, response, decoded, pid=None):
    entry = {
        "status": "ok",
        "kind": kind,
        "request": request,
        "response_index": response.response_index,
        "raw_hex": _raw_hex(response.values),
    }
    if pid is not None:
        entry["pid"] = pid
    if isinstance(decoded, MonitorStatus):
        entry.update(decoded.__dict__)
    elif isinstance(decoded, Measurement):
        entry.update(decoded.__dict__)
    elif kind in {"dtcs", "pending_dtcs", "permanent_dtcs"}:
        entry["codes"] = decoded
    else:
        entry["supported_pids"] = decoded
    results.append(entry)


def collect_read_only_snapshot(adapter: Elm327Adapter) -> List[Dict[str, object]]:
    """Collect a capability-gated, read-only OBD-II snapshot.

    Supported-PID bitmaps (0100/0120/0140) are read first; only advertised
    live-data PIDs are requested afterwards. Multiple ECU responses are
    recorded separately. ELM headers are disabled, so ``response_index`` is an
    ordering hint, not a verified ECU identity.
    """
    results: List[Dict[str, object]] = []
    supported = set()

    bitmaps = ((0x00, "0100"), (0x20, "0120"), (0x40, "0140"))
    for index, (base_pid, request) in enumerate(bitmaps):
        if index and base_pid not in supported:
            break
        try:
            responses = adapter.request_obd(request)
        except DiagnosticError as error:
            _append_error(results, "capabilities", request, error)
            break
        for response in responses:
            try:
                pids = decode_supported_pids(response.values, base_pid)
            except DiagnosticError as error:
                _append_error(results, "capabilities", request, error, response)
                continue
            supported.update(pids)
            _append_decoded(results, "capabilities", request, response, pids, pid=base_pid)

    if supported:
        live_pids = [pid for pid in LIVE_PID_ORDER if pid in supported]
    else:
        # A clone that cannot answer 0100 still gets a minimal common set.
        live_pids = [0x01, 0x05, 0x0C, 0x0D, 0x0F]

    for pid in live_pids:
        request = "01{:02X}".format(pid)
        kind = "monitors" if pid == 0x01 else "measurement"
        try:
            responses = adapter.request_obd(request)
        except DiagnosticError as error:
            _append_error(results, kind, request, error)
            continue
        for response in responses:
            try:
                decoded = PID_DECODERS[pid](response.values)
            except DiagnosticError as error:
                _append_error(results, kind, request, error, response)
                continue
            _append_decoded(results, kind, request, response, decoded, pid=pid)

    dtc_requests = (
        ("dtcs", "03", decode_dtc_response),
        ("pending_dtcs", "07", decode_pending_dtc_response),
        ("permanent_dtcs", "0A", decode_permanent_dtc_response),
    )
    for kind, request, decoder in dtc_requests:
        try:
            responses = adapter.request_obd(request)
        except DiagnosticError as error:
            _append_error(results, kind, request, error)
            continue
        for response in responses:
            try:
                decoded = decoder(response.values)
            except DiagnosticError as error:
                _append_error(results, kind, request, error, response)
                continue
            _append_decoded(results, kind, request, response, decoded)
    return results


def _parse_tcp_endpoint(value: str) -> Tuple[str, int]:
    host, separator, port_text = value.rpartition(":")
    if not separator or not host or not port_text.isdigit():
        raise argparse.ArgumentTypeError("expected HOST:PORT, for example 192.168.0.10:35000")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return host, port


def _adapter_info(capabilities: AdapterCapabilities, protocol: str, transport: str) -> Dict[str, str]:
    return {
        "version": capabilities.version,
        "description": capabilities.description,
        "protocol": protocol,
        "transport": transport,
        "voltage": capabilities.initialization.get("ATRV", "unknown"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OpenVAG read-only OBD-II prototype")
    endpoint_group = parser.add_mutually_exclusive_group()
    endpoint_group.add_argument(
        "--simulate",
        action="store_true",
        help="run deterministic simulated responses instead of hardware",
    )
    endpoint_group.add_argument(
        "--tcp",
        metavar="HOST:PORT",
        type=_parse_tcp_endpoint,
        help="connect to an ELM327 Wi-Fi bridge over TCP (real, read-only requests)",
    )
    endpoint_group.add_argument(
        "--serial",
        metavar="PORT",
        help="connect to an ELM327 Bluetooth/USB serial port (requires .[serial])",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=38400,
        metavar="RATE",
        help="serial baud rate for --serial (default: 38400)",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="list serial ports (requires .[serial]) and exit",
    )
    parser.add_argument("--session", type=Path, help="write a JSON session")
    args = parser.parse_args(argv)

    if args.list_ports:
        if args.simulate or args.tcp or args.serial:
            parser.error("--list-ports cannot be combined with a connection option")
        try:
            ports = list_serial_ports()
        except DiagnosticError as error:
            print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
            return 1
        print(json.dumps({"serial_ports": ports}, indent=2))
        return 0

    if not (args.simulate or args.tcp or args.serial):
        parser.error("choose one of --simulate, --tcp, or --serial")
    if args.baud <= 0:
        parser.error("--baud must be positive")

    if args.simulate:
        source = "simulator"
        transport_name = "simulator"
        transport = SimulatedElm327Transport()
    elif args.tcp:
        source = "real"
        transport_name = "tcp"
        host, port = args.tcp
        transport = TcpLineTransport(host, port)
    else:
        source = "real"
        transport_name = "serial"
        transport = SerialLineTransport(args.serial, baudrate=args.baud)

    adapter = Elm327Adapter(transport)
    try:
        capabilities = adapter.connect()
        results = collect_read_only_snapshot(adapter)
        protocol = adapter.describe_protocol()
        adapter_info = _adapter_info(capabilities, protocol, transport_name)
        session = DiagnosticSession.create(
            source,
            capabilities.version,
            results,
            adapter=adapter_info,
        )
        if args.session:
            session.save(args.session)
        print(json.dumps({"source": source, "adapter": adapter_info, "results": results}, indent=2))
        return 0
    except DiagnosticError as error:
        print(json.dumps({"source": source, "error": str(error)}, indent=2), file=sys.stderr)
        return 1
    except OSError as error:
        print(
            json.dumps({"source": source, "error": "cannot write session: {}".format(error)}, indent=2),
            file=sys.stderr,
        )
        return 1
    finally:
        adapter.close()


if __name__ == "__main__":
    raise SystemExit(main())
