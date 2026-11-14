"""CLI entry point. Only simulated mode is available until a serial backend is validated."""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .elm327 import Elm327Adapter
from .errors import DiagnosticError, ServiceUnsupportedError
from .obd import decode_dtc_response, decode_engine_rpm, decode_supported_pids, decode_vehicle_speed
from .session import DiagnosticSession
from .simulator import SimulatedElm327Transport


def collect_read_only_snapshot(adapter: Elm327Adapter) -> List[Dict[str, object]]:
    """Collect each prototype request independently, retaining normalized errors."""
    results = []
    requests = (
        ("capabilities", "0100", decode_supported_pids),
        ("measurement", "010C", decode_engine_rpm),
        ("measurement", "010D", decode_vehicle_speed),
        ("dtcs", "03", decode_dtc_response),
    )
    for kind, request, decoder in requests:
        try:
            decoded = decoder(adapter.request_obd(request))
            if kind == "measurement":
                results.append({"status": "ok", "kind": kind, **decoded.__dict__})
            elif kind == "capabilities":
                results.append({"status": "ok", "kind": kind, "request": request, "supported_pids": decoded})
            else:
                results.append({"status": "ok", "kind": kind, "request": request, "codes": decoded})
        except DiagnosticError as error:
            status = "unsupported" if isinstance(error, ServiceUnsupportedError) else "failed"
            results.append({"status": status, "kind": kind, "request": request, "error": str(error)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenVAG read-only OBD-II prototype")
    parser.add_argument("--simulate", action="store_true", help="run deterministic simulated responses")
    parser.add_argument("--session", type=Path, help="write a JSON session (contains no VIN in simulated mode)")
    args = parser.parse_args()
    if not args.simulate:
        parser.error("no hardware backend is implemented; use --simulate")
    adapter = Elm327Adapter(SimulatedElm327Transport())
    capabilities = adapter.connect()
    results = collect_read_only_snapshot(adapter)
    session = DiagnosticSession.create("simulator", capabilities.version, results)
    if args.session:
        session.save(args.session)
    print(json.dumps({"source": session.source, "results": results}, indent=2))
    adapter.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
