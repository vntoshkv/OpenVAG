# OpenVAG Diagnostic

**OpenVAG Diagnostic** is a provisional working name for an independent,
open-source diagnostic platform focused initially on Volkswagen Group (VAG)
vehicles.

The long-term goal is a community-developed toolset for communicating with
vehicle ECUs, interpreting diagnostic data, recording sessions, and sharing
verified vehicle knowledge. It is not an official Volkswagen, Audi, or
Ross-Tech product and is not affiliated with those companies.

> **Project status:** an initial simulated, read-only OBD-II vertical slice
> exists. A Wi-Fi TCP transport is implemented, but no hardware run has been
> verified. Adapter compatibility, vehicle support, and data coverage are not
> finalized. The code is licensed under Apache-2.0. Do not infer real-vehicle
> support from simulator results.

**Repository:** <https://github.com/vntoshkv/OpenVAG>

## What the project is

OpenVAG Diagnostic aims to be a transparent, testable, adapter-independent
diagnostic platform. It is built from documented standards, public
information, independently gathered measurements, and permissively licensed
components — not from proprietary VCDS/ODIS internals or copied databases.

Core principles:

- read-only by default; any ECU write is a separate, reviewed, gated feature;
- separate transport/protocol code from vehicle-specific knowledge;
- keep unknown values explicitly unknown, with provenance and verification
  status;
- support simulator-driven development without presenting simulation as
  vehicle data.

## Initial validation target

- Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA.
- ELM327-compatible adapters over Wi-Fi and Bluetooth classic.
- Adapter models, firmware, and compatibility are unverified.

This is the first validation target, not a limit on the intended scope.

## Current prototype

The repository contains a dependency-free Python prototype with:

- a small read-only ELM327 command boundary with echo/chatter normalization,
  separate handling of multiple ECU responses, and explicit error
  classification;
- adapter identification (`ATI`, `AT@1`, `ATDPN`, `ATRV`) and per-command
  timeouts;
- a deterministic simulator;
- capability-gated standard OBD-II data: supported-PID bitmaps (0100/0120/0140),
  monitor status, common live-data PIDs, and stored, pending, and permanent
  DTCs (03/07/0A), with raw response hex retained;
- a Wi-Fi TCP transport for ELM327 bridges;
- a serial transport for Bluetooth classic and USB adapters, using an optional
  `pyserial` extra; and
- JSON session records with adapter metadata.

It sends only a fixed allowlist of standard read-only requests. It cannot clear
DTCs or send coding, adaptation, actuator, or security-access requests. Each
request is recorded independently, so an unsupported, negative, malformed, or
failed request does not discard successful results. The exact PID coverage and
formulas are listed in [`docs/OBD_PIDS.md`](docs/OBD_PIDS.md).

The Wi-Fi transport is covered by loopback tests and the serial transport by
fake-device tests. No real adapter has been verified against a vehicle, and
the included simulated data must never be represented as vehicle data.

## One-command collection

On macOS/Linux, run the collector from the repository root:

```shell
./collect.sh
```

It creates/uses `.venv`, installs the optional serial extra, prompts before
each adapter step, and writes a combined JSON log plus a Markdown summary to
`logs/`:

- `logs/collect-YYYYMMDD-HHMMSS.json` — full snapshot, including raw response
  hex;
- `logs/collect-YYYYMMDD-HHMMSS.md` — adapter summary, live data, DTCs, and
  non-ok results.

The script is read-only and never sends coding, adaptation, actuator, or
security-access requests. `logs/` is git-ignored. It cannot join the Wi-Fi
network or pair Bluetooth for you; it pauses and asks you to do that.

Useful flags:

```shell
./collect.sh --no-serial                  # Wi-Fi only
./collect.sh --no-wifi                    # Bluetooth only, auto-detect port
./collect.sh --no-wifi --serial /dev/cu.ELM327-XXXX
./collect.sh --yes                        # do not pause before each step
```

If you prefer to manage the environment yourself, the manual commands are
below. The cross-platform entry point is
[`scripts/collect_logs.py`](scripts/collect_logs.py).

## Quick start

```shell
git clone https://github.com/vntoshkv/OpenVAG.git
cd OpenVAG
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m openvag.cli --simulate --session simulated-session.json
```

Real Wi-Fi adapter (read-only; join the adapter's access point first). The
address and port vary by device; an ELM327 Wi-Fi bridge commonly uses
`192.168.0.10:35000`:

```shell
PYTHONPATH=src python3 -m openvag.cli --tcp 192.168.0.10:35000 --session wifi-session.json
```

No real adapter has been verified yet; see [`docs/HARDWARE.md`](docs/HARDWARE.md).

Bluetooth classic adapters appear as OS serial devices after pairing. A virtual
environment is recommended so the system Python is not modified:

```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[serial]'
PYTHONPATH=src python3 -m openvag.cli --list-ports
PYTHONPATH=src python3 -m openvag.cli --serial /dev/cu.ELM327-XXXX --baud 38400 --session bluetooth-session.json
```

On macOS the port is usually `/dev/cu.*`; the default baud rate is 38400, but
confirm it for the specific adapter. The same backend works for USB serial
ELM327 adapters.

Editable install (provides the `openvag` console script):

```shell
python3 -m pip install -e .
openvag --simulate
```

## Planned direction

1. Validate the Wi-Fi and Bluetooth transports against the real adapters.
2. Define a versioned session format with explicit data source and redaction.
3. Extend the capability-gated snapshot beyond the current curated PID set.
4. Investigate VAG module access separately; do not assume the ELM327 is a
   general ISO-TP/UDS transport.
5. Add a versioned vehicle/ECU knowledge schema with provenance.

Advanced functions such as coding, adaptations, actuator tests, and security
access remain out of scope until the read-only foundation is stable and each
one receives a separate safety review.

## Documentation

- [`AGENTS.md`](AGENTS.md) — repository instructions for AI coding agents.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution workflow.
- [`docs/PROJECT_VISION.md`](docs/PROJECT_VISION.md) — goals, scope, principles.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — intended system boundaries.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged development plan.
- [`docs/DATA_AND_SAFETY.md`](docs/DATA_AND_SAFETY.md) — provenance, verification, privacy, safety.
- [`docs/OBD_PIDS.md`](docs/OBD_PIDS.md) — supported OBD-II PIDs, formulas, units, and verification status.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — decisions and open questions.
- [`docs/HARDWARE.md`](docs/HARDWARE.md) — reference hardware and identification procedure.
- [`docs/DEPENDENCY_REVIEW.md`](docs/DEPENDENCY_REVIEW.md) — dependency and license review.

## License

The project is licensed under the **Apache License, Version 2.0**. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). You may use, modify, and
distribute the code, including for commercial purposes, under the terms of
that license.

Third-party components, when added, retain their own licenses and notices;
see [`docs/DEPENDENCY_REVIEW.md`](docs/DEPENDENCY_REVIEW.md). GPL-family code
is not combined with this project because of license incompatibility.
