# OpenVAG Diagnostic

**OpenVAG Diagnostic** is a provisional working name for an independent,
open-source diagnostic platform focused initially on Volkswagen Group (VAG)
vehicles.

The long-term goal is a community-developed toolset for communicating with
vehicle ECUs, interpreting diagnostic data, recording sessions, and sharing
verified vehicle knowledge. It is not an official Volkswagen, Audi, or
Ross-Tech product and is not affiliated with those companies.

> **Project status:** an initial simulated, read-only OBD-II vertical slice
> exists. There is no hardware backend yet. Adapter compatibility, vehicle
> support, and data coverage are not finalized. The code is licensed under
> Apache-2.0. Do not infer real-vehicle support from simulator results.

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

- a small read-only ELM327 command boundary;
- a deterministic simulator;
- standard OBD-II decoding for supported-PID capability bits, engine RPM,
  vehicle speed, and stored DTCs;
- JSON session records; and
- a simulator-only CLI.

It accepts only the read-only requests `0100`, `010C`, `010D`, and `03`. It
cannot clear DTCs or send other diagnostic requests. Each request is recorded
independently, so an unsupported or failed request does not discard successful
results.

There is deliberately no serial, TCP, or Bluetooth backend yet. The included
simulated data must never be represented as vehicle data.

## Quick start

```shell
git clone https://github.com/vntoshkv/OpenVAG.git
cd OpenVAG
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m openvag.cli --simulate --session simulated-session.json
```

Editable install (provides the `openvag` console script):

```shell
python3 -m pip install -e .
openvag --simulate
```

## Planned direction

1. Harden the ELM327 response boundary (echo, adapter chatter, multiple ECU
   responses, timeout and error classification).
2. Add a Wi-Fi TCP transport, then Bluetooth classic as an OS serial device.
3. Define a versioned session format with explicit data source and redaction.
4. Expand capability-gated read-only OBD-II coverage.
5. Investigate VAG module access separately; do not assume the ELM327 is a
   general ISO-TP/UDS transport.
6. Add a versioned vehicle/ECU knowledge schema with provenance.

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
