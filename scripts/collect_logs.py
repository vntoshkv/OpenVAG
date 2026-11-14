#!/usr/bin/env python3
"""Collect read-only OBD-II snapshots from Wi-Fi and Bluetooth ELM327 adapters.

Usage examples:
    python3 scripts/collect_logs.py
    python3 scripts/collect_logs.py --no-serial
    python3 scripts/collect_logs.py --no-wifi --serial /dev/cu.ELM327-XXXX
    python3 scripts/collect_logs.py --wifi 192.168.0.10:35000 --yes

The script prompts before each adapter step because joining the Wi-Fi access
point and pairing Bluetooth are operating-system actions it must not perform
silently. Results are written to logs/ as JSON plus a Markdown summary.
No write, coding, adaptation, actuator, or security-access request is sent.
"""

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import openvag  # noqa: E402
from openvag.cli import collect_read_only_snapshot  # noqa: E402
from openvag.elm327 import AdapterCapabilities, Elm327Adapter  # noqa: E402
from openvag.errors import AdapterUnavailableError, DiagnosticError  # noqa: E402
from openvag.serial_transport import SerialLineTransport, list_serial_ports  # noqa: E402
from openvag.tcp_transport import TcpLineTransport  # noqa: E402

_EXCLUDED_PORT_HINTS = (
    "incoming",
    "debug",
    "headphone",
    "freebuds",
    "airpods",
    "handsfree",
    "hfp",
    "sound",
)
_ELM_PORT_HINTS = ("elm", "obd", "vlink", "v-link", "vag", "kkl", "serial", "usbserial", "ch340", "cp210", "ftdi")


def parse_endpoint(value: str) -> Tuple[str, int]:
    host, separator, port_text = value.rpartition(":")
    if not separator or not host or not port_text.isdigit():
        raise argparse.ArgumentTypeError("expected HOST:PORT, for example 192.168.0.10:35000")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return host, port


def adapter_info(capabilities: AdapterCapabilities, protocol: str, transport: str) -> Dict[str, str]:
    return {
        "version": capabilities.version,
        "description": capabilities.description,
        "protocol": protocol,
        "transport": transport,
        "voltage": capabilities.initialization.get("ATRV", "unknown"),
    }


def count_statuses(results: List[Dict[str, object]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for result in results:
        status = str(result.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def supported_pids(results: List[Dict[str, object]]) -> List[int]:
    pids = set()
    for result in results:
        if result.get("kind") == "capabilities":
            pids.update(result.get("supported_pids", []))
    return sorted(pids)


def dtc_summary(results: List[Dict[str, object]]) -> Dict[str, List[str]]:
    summary: Dict[str, List[str]] = {}
    for kind in ("dtcs", "pending_dtcs", "permanent_dtcs"):
        codes = set()
        for result in results:
            if result.get("kind") == kind:
                codes.update(result.get("codes", []))
        summary[kind] = sorted(codes)
    return summary


def run_snapshot(transport, transport_name: str, endpoint: str) -> Dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    adapter = Elm327Adapter(transport)
    status = "error"
    error: Optional[str] = None
    results: List[Dict[str, object]] = []
    info: Dict[str, str] = {}
    try:
        capabilities = adapter.connect()
        results = collect_read_only_snapshot(adapter)
        protocol = adapter.describe_protocol()
        info = adapter_info(capabilities, protocol, transport_name)
        counts = count_statuses(results)
        status = "ok" if counts.get("ok", 0) else "failed"
    except DiagnosticError as exc:
        error = str(exc)
        counts = {}
    except OSError as exc:
        error = "I/O error: {}".format(exc)
        counts = {}
    except ValueError as exc:
        error = "invalid configuration: {}".format(exc)
        counts = {}
    finally:
        adapter.close()
    duration = round(time.monotonic() - started, 3)
    return {
        "transport": transport_name,
        "endpoint": endpoint,
        "status": status,
        "error": error,
        "started_at": started_at,
        "duration_s": duration,
        "adapter": info,
        "counts": counts if status != "error" else {},
        "supported_pids": supported_pids(results),
        "dtcs": dtc_summary(results),
        "results": results,
    }


def detect_serial_port(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    try:
        ports = list_serial_ports()
    except AdapterUnavailableError as exc:
        raise AdapterUnavailableError(str(exc)) from exc
    candidates = [port for port in ports if not any(hint in port.lower() for hint in _EXCLUDED_PORT_HINTS)]
    matches = [port for port in candidates if any(hint in port.lower() for hint in _ELM_PORT_HINTS)]
    choices = matches or candidates or ports
    if len(choices) == 1:
        return choices[0]
    if not choices:
        raise AdapterUnavailableError(
            "no serial ports found; pair the Bluetooth adapter first and check /dev/cu.*"
        )
    if not sys.stdin.isatty():
        raise AdapterUnavailableError(
            "multiple serial ports; pass --serial explicitly: {}".format(", ".join(choices))
        )
    print("Serial ports:")
    for index, port in enumerate(choices, start=1):
        print("  {}. {}".format(index, port))
    selection = input("Choose a port number: ").strip()
    if not selection.isdigit() or not 1 <= int(selection) <= len(choices):
        raise AdapterUnavailableError("invalid serial-port selection")
    return choices[int(selection) - 1]


def wait_for_user(message: str, assume_yes: bool) -> None:
    print(message)
    if assume_yes or not sys.stdin.isatty():
        return
    input("Press Enter when ready... ")


def _format_value(value) -> str:
    if isinstance(value, float):
        return "{:.3f}".format(value)
    return str(value)


def render_markdown(combined: Dict[str, object]) -> str:
    lines = [
        "# OpenVAG read-only collection",
        "",
        "Generated: `{}`".format(combined["created_at"]),
        "Environment: {} {} | Python {}".format(
            combined["environment"]["system"],
            combined["environment"]["machine"],
            combined["environment"]["python"],
        ),
        "",
        "> Read-only standard OBD-II snapshot. No VIN was requested. Raw responses",
        "> are retained; treat logs as potentially vehicle-related data.",
        "",
        "## Summary",
        "",
        "| transport | endpoint | status | protocol | ok | other |",
        "|---|---|---|---|---|---|",
    ]
    for run in combined["runs"]:
        counts = run.get("counts", {})
        ok = counts.get("ok", 0)
        other = sum(value for key, value in counts.items() if key != "ok")
        protocol = run.get("adapter", {}).get("protocol", "—")
        lines.append(
            "| {} | `{}` | {} | {} | {} | {} |".format(
                run["transport"], run["endpoint"], run["status"], protocol, ok, other
            )
        )

    for run in combined["runs"]:
        lines.extend(["", "## {} — `{}`".format(run["transport"], run["endpoint"]), ""])
        if run["error"]:
            lines.append("**Error:** {}".format(run["error"]))
            continue
        adapter = run.get("adapter", {})
        lines.append(
            "- Adapter: {} | {} | protocol {} | transport {} | {}".format(
                adapter.get("version", "unknown"),
                adapter.get("description", "unknown"),
                adapter.get("protocol", "unknown"),
                adapter.get("transport", run["transport"]),
                adapter.get("voltage", "unknown"),
            )
        )
        lines.append("- Duration: {} s".format(run["duration_s"]))
        lines.append("- Status counts: `{}`".format(json.dumps(run["counts"], sort_keys=True)))
        lines.append(
            "- Supported PIDs: {}".format(
                ", ".join(str(pid) for pid in run["supported_pids"]) or "none reported"
            )
        )
        dtcs = run["dtcs"]
        lines.append(
            "- DTCs: stored={}, pending={}, permanent={}".format(
                dtcs["dtcs"], dtcs["pending_dtcs"], dtcs["permanent_dtcs"]
            )
        )

        measurements = [
            result
            for result in run["results"]
            if result.get("status") == "ok" and result.get("kind") in {"measurement", "monitors"}
        ]
        if measurements:
            lines.extend(["", "### Live data", "", "| request | name | value | unit | raw |", "|---|---|---|---|---|"])
            for result in measurements:
                if result.get("kind") == "monitors":
                    name = "monitor_status"
                    value = "MIL={} DTCs={}".format(result.get("mil_on"), result.get("dtc_count"))
                    unit = ""
                else:
                    name = result.get("name", "unknown")
                    value = _format_value(result.get("value"))
                    unit = result.get("unit", "")
                lines.append(
                    "| `{}` | {} | {} | {} | `{}` |".format(
                        result.get("request"), name, value, unit, result.get("raw_hex", "")
                    )
                )

        failures = [result for result in run["results"] if result.get("status") != "ok"]
        if failures:
            lines.extend(["", "### Non-ok results", "", "| request | status | error |", "|---|---|---|"])
            for result in failures:
                lines.append(
                    "| `{}` | {} | {} |".format(
                        result.get("request"), result.get("status"), result.get("error", "")
                    )
                )
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Collect read-only ELM327 snapshots from Wi-Fi and Bluetooth")
    parser.add_argument(
        "--wifi",
        metavar="HOST:PORT",
        type=parse_endpoint,
        default=parse_endpoint("192.168.0.10:35000"),
        help="Wi-Fi ELM327 TCP endpoint (default: 192.168.0.10:35000)",
    )
    parser.add_argument("--no-wifi", action="store_true", help="skip the Wi-Fi adapter")
    parser.add_argument("--serial", metavar="PORT", help="Bluetooth/USB serial port; auto-detected if omitted")
    parser.add_argument("--no-serial", action="store_true", help="skip the Bluetooth/USB adapter")
    parser.add_argument("--baud", type=int, default=38400, help="serial baud rate (default: 38400)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "logs",
        help="directory for JSON/Markdown logs (default: <repo>/logs)",
    )
    parser.add_argument("--yes", action="store_true", help="do not pause before each adapter step")
    args = parser.parse_args(argv)

    if args.no_wifi and args.no_serial:
        parser.error("both adapters are disabled; nothing to do")
    if args.no_serial and args.serial:
        parser.error("--serial cannot be combined with --no-serial")
    if args.baud <= 0:
        parser.error("--baud must be positive")

    created_at = datetime.now(timezone.utc).isoformat()
    runs: List[Dict[str, object]] = []

    if not args.no_wifi:
        wait_for_user(
            "1) Join the ELM327 Wi-Fi access point (commonly 192.168.0.10).", args.yes
        )
        host, port = args.wifi
        runs.append(run_snapshot(TcpLineTransport(host, port), "tcp", "{}:{}".format(host, port)))

    if not args.no_serial:
        wait_for_user(
            "2) Pair the Bluetooth adapter and make sure its /dev/cu.* port exists.", args.yes
        )
        try:
            serial_port = detect_serial_port(args.serial)
        except DiagnosticError as exc:
            runs.append(
                {
                    "transport": "serial",
                    "endpoint": args.serial or "auto",
                    "status": "error",
                    "error": str(exc),
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "duration_s": 0,
                    "adapter": {},
                    "counts": {},
                    "supported_pids": [],
                    "dtcs": {"dtcs": [], "pending_dtcs": [], "permanent_dtcs": []},
                    "results": [],
                }
            )
        else:
            runs.append(
                run_snapshot(
                    SerialLineTransport(serial_port, baudrate=args.baud),
                    "serial",
                    "{}@{} baud".format(serial_port, args.baud),
                )
            )

    combined = {
        "schema": "openvag-collect-1",
        "created_at": created_at,
        "environment": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "openvag": openvag.__version__,
        },
        "runs": runs,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "collect-{}.json".format(stamp)
    markdown_path = output_dir / "collect-{}.md".format(stamp)
    json_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(combined), encoding="utf-8")

    print("\nWrote:")
    print("  {}".format(json_path))
    print("  {}".format(markdown_path))
    for run in runs:
        counts = run.get("counts", {})
        print(
            "  {}: {} (ok={}, other={})".format(
                run["transport"],
                run["status"],
                counts.get("ok", 0),
                sum(value for key, value in counts.items() if key != "ok"),
            )
        )
    return 0 if any(run["status"] == "ok" for run in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
