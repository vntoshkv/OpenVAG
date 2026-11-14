"""CLI entry point: deterministic simulator or a real Wi-Fi ELM327 bridge."""

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
from .obd import decode_dtc_response, decode_engine_rpm, decode_supported_pids, decode_vehicle_speed
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


def collect_read_only_snapshot(adapter: Elm327Adapter) -> List[Dict[str, object]]:
    """Collect each prototype request independently, retaining normalized errors.

    Multiple ECU responses are recorded separately. ELM headers are disabled,
    so ``response_index`` is an ordering hint, not a verified ECU identity.
    """
    results: List[Dict[str, object]] = []
    requests = (
        ("capabilities", "0100", decode_supported_pids),
        ("measurement", "010C", decode_engine_rpm),
        ("measurement", "010D", decode_vehicle_speed),
        ("dtcs", "03", decode_dtc_response),
    )
    for kind, request, decoder in requests:
        try:
            responses = adapter.request_obd(request)
        except DiagnosticError as error:
            results.append(
                {
                    "status": _status_for(error),
                    "kind": kind,
                    "request": request,
                    "error": str(error),
                }
            )
            continue

        for response in responses:
            try:
                decoded = decoder(response.values)
            except DiagnosticError as error:
                results.append(
                    {
                        "status": _status_for(error),
                        "kind": kind,
                        "request": request,
                        "response_index": response.response_index,
                        "error": str(error),
                    }
                )
                continue

            entry: Dict[str, object] = {
                "status": "ok",
                "kind": kind,
                "request": request,
                "response_index": response.response_index,
            }
            if kind == "measurement":
                entry.update(decoded.__dict__)
            elif kind == "capabilities":
                entry["supported_pids"] = decoded
            else:
                entry["codes"] = decoded
            results.append(entry)
    return results


def _parse_tcp_endpoint(value: str) -> Tuple[str, int]:
    host, separator, port_text = value.rpartition(":")
    if not separator or not host or not port_text.isdigit():
        raise argparse.ArgumentTypeError("expected HOST:PORT, for example 192.168.0.10:35000")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return host, port


def _adapter_info(capabilities: AdapterCapabilities, protocol: str) -> Dict[str, str]:
    return {
        "version": capabilities.version,
        "description": capabilities.description,
        "protocol": protocol,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OpenVAG read-only OBD-II prototype")
    endpoint_group = parser.add_mutually_exclusive_group(required=True)
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
    parser.add_argument("--session", type=Path, help="write a JSON session")
    args = parser.parse_args(argv)

    source = "simulator" if args.simulate else "real"
    if args.simulate:
        transport = SimulatedElm327Transport()
    else:
        host, port = args.tcp
        transport = TcpLineTransport(host, port)

    adapter = Elm327Adapter(transport)
    try:
        capabilities = adapter.connect()
        results = collect_read_only_snapshot(adapter)
        protocol = adapter.describe_protocol()
        adapter_info = _adapter_info(capabilities, protocol)
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
