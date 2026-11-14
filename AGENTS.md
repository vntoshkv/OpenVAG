# Instructions for AI agents

This file is the entry point. Read it fully, then load only the documents
relevant to the task (see **Task routing**). Do not preload the whole `docs/`
tree for every task.

## Project snapshot (last verified 2026-11-14)

- **Working name:** OpenVAG Diagnostic. Provisional; not affiliated with
  Volkswagen, Audi, or Ross-Tech.
- **License:** Apache-2.0 (`LICENSE`, `NOTICE`). Public repository:
  <https://github.com/vntoshkv/OpenVAG>, branch `main`.
- **Goal:** independent, community-maintained diagnostic platform for VAG
  vehicles; architecture may later support other makes.
- **Validation target:** Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA.
- **Available hardware:** ELM327 over Wi-Fi and ELM327 over Bluetooth classic;
  models, firmware, and clone behavior are unverified. A Chinese USB
  VCDS-compatible cable is not confirmed to be available. No real adapter or
  vehicle test has been completed.
- **Runtime:** Python >=3.9 (3.9 is EOL; floor under review), standard-library
  core, optional `pyserial` extra for Bluetooth/USB serial.
- **Implemented:**
  - read-only ELM327 boundary with echo/chatter normalization, multi-ECU
    responses, adapter identification, and error classification;
  - deterministic simulator;
  - Wi-Fi TCP and Bluetooth/USB serial transports;
  - capability-gated OBD-II snapshot: `0100/0120/0140`, monitor status,
    curated mode 01 live data, stored/pending/permanent DTCs (`03/07/0A`),
    raw response hex;
  - CLI and one-command collector (`./collect.sh` → `scripts/collect_logs.py`)
    writing JSON and Markdown under `logs/` (git-ignored).
- **Not implemented:** freeze frame (`02`), mode 06, mode 09 identifiers,
  O2-sensor PIDs, full readiness-bit semantics, VAG module/UDS access, session
  schema/reporting, desktop UI, and any write/coding/adaptation/actuator/
  security-access operation.
- **Tests/CI:** `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  (46 tests at last check). GitHub Actions runs Linux/Windows/macOS on
  Python 3.9/3.12; hardware is never tested in CI.

If this snapshot conflicts with code or tests, code/tests win. Update this file
when behavior, safety assumptions, or the project status materially change.

## Before making changes

1. Inspect the relevant existing code and tests. Do not assume a planned module
   exists.
2. Identify the smallest useful change; implement it and add or update tests.
3. Read only the routed documents for the task, not all of `docs/`.
4. State what was actually tested. Never claim hardware compatibility without
   an observed transcript from the named device and vehicle configuration.
5. If a requirement is ambiguous or could cause an ECU write, stop and ask.

## Commands

```shell
# Tests (no hardware, no third-party dependency)
PYTHONPATH=src python3 -m unittest discover -s tests -v

# Simulator
PYTHONPATH=src python3 -m openvag.cli --simulate --session /tmp/session.json

# Real Wi-Fi ELM327
PYTHONPATH=src python3 -m openvag.cli --tcp 192.168.0.10:35000 --session /tmp/wifi.json

# Real Bluetooth/USB ELM327 (needs: python -m pip install -e '.[serial]')
PYTHONPATH=src python3 -m openvag.cli --list-ports
PYTHONPATH=src python3 -m openvag.cli --serial /dev/cu.ELM327-XXXX --baud 38400 --session /tmp/bt.json

# One command for both adapters, with logs/
./collect.sh

# Hardware-free dry run through the same log path
./collect.sh --simulate
```

`collect.sh` bootstraps `.venv`, installs the serial extra once, prompts for
each adapter, and writes `logs/collect-*.json` and `.md`. Never commit `.venv`
or `logs/`.

## Source map

| File | Responsibility |
|---|---|
| `src/openvag/transport.py` | `LineTransport` contract: response lines, no prompt |
| `src/openvag/elm327.py` | Read-only allowlist, ELM normalization, timeouts, adapter info |
| `src/openvag/obd.py` | Standard OBD-II PID/bitmap/DTC decoders |
| `src/openvag/tcp_transport.py` | Wi-Fi TCP bridge |
| `src/openvag/serial_transport.py` | Bluetooth/USB serial; lazy optional pyserial |
| `src/openvag/simulator.py` | Deterministic test/CLI fixtures |
| `src/openvag/session.py` | JSON session record |
| `src/openvag/cli.py` | Snapshot collection, CLI, error/status mapping |
| `scripts/collect_logs.py`, `collect.sh` | Interactive two-adapter collector and logs |
| `tests/` | Unit, simulator, loopback TCP, fake-serial, CLI/collector tests |

Data flow: CLI/collector → `Elm327Adapter` → `LineTransport` → ELM327 → ECU.
Decoders consume one ECU response at a time. `response_index` is an ordering
hint only; ELM headers are disabled (`ATH0`), so it is not a verified ECU ID.

## Non-negotiable safety and legal constraints

- **Read-only by default.** The request allowlist lives in `elm327.py`. Any
  write, coding, adaptation, actuator test, routine control, security access,
  or ECU reset requires a separate design, explicit user intent, logging, and
  safety review. Do not implement such operations opportunistically.
- **No guessing.** Do not invent ECU addresses, diagnostic identifiers, PID
  formulas, scaling, byte order, units, or vehicle applicability. Unknown
  values stay explicitly unknown.
- **No simulation as vehicle data.** Every result source must be labelled
  (`real`, `simulator`, `mock`, imported recording).
- **Hardware is unverified.** A successful simulator, loopback, or fake-device
  test is not vehicle compatibility. Hardware tests are manual and opt-in.
- **Independence.** Do not decompile, disassemble, extract proprietary
  databases from, or copy closed-source VCDS/ODIS internals. Do not copy code
  or data without a compatible license and recorded provenance. GPL-family code
  is incompatible with this Apache-2.0 project.
- **Privacy.** Never commit VINs, registration plates, customer records,
  access keys, raw logs with personal data, or secrets. Sessions and logs can
  contain vehicle-related data; keep them out of the repository.
- **Dependencies.** The core is dependency-free. Add a dependency only with a
  recorded reason, license/maintenance check, and preferably an optional extra.
  See `docs/DEPENDENCY_REVIEW.md`.

## Data rules

- Every vehicle-specific definition needs source/provenance, applicability,
  units/formula/byte order, verification state, and known limits.
- Use the verification vocabulary in `docs/DATA_AND_SAFETY.md`. The current
  standard PIDs are `simulator-tested`, not vehicle-verified.
- Request PIDs only when advertised by the supported-PID bitmap. Preserve raw
  response hex for evidence; do not silently drop failed/unsupported requests.

## Task routing

| Task | Read only |
|---|---|
| Add/change a PID or decoder | `docs/OBD_PIDS.md`, `docs/DATA_AND_SAFETY.md`, `src/openvag/obd.py`, relevant tests |
| Transport/adapter behavior | `docs/ARCHITECTURE.md`, `docs/HARDWARE.md`, `docs/DECISIONS.md` (D-010), transport code |
| Session format, redaction, export | `docs/DATA_AND_SAFETY.md`, `docs/ROADMAP.md` (M2/M3), `docs/DECISIONS.md` (O-006) |
| VAG modules, UDS, recon | `docs/PROJECT_VISION.md`, `docs/ROADMAP.md` (M3/M6), `docs/DECISIONS.md`; recon first, no guessed addresses |
| Licensing/dependencies/data provenance | `docs/DEPENDENCY_REVIEW.md`, `LICENSE`, `NOTICE`, `AGENTS.md` rules above |
| User-facing overview/commands | `README.md` (only when needed) |
| Car-day preparation or log collection | `docs/CAR_DAY.md`, `docs/HARDWARE.md`, collector code |
| Safety change or write proposal | Stop and ask; then `docs/DATA_AND_SAFETY.md` + `docs/ARCHITECTURE.md` |

Do not read `docs/PROJECT_VISION.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`,
`docs/DATA_AND_SAFETY.md`, and `docs/DECISIONS.md` all at once by habit. The
routing table exists to keep context small.

## Workflow and definition of done

- Start non-trivial changes with a brief plan; keep increments small and
  reviewable.
- Add unit tests for pure logic and simulator/loopback/fake-device integration
  tests for protocol behavior. Hardware tests must not run in CI.
- Update docs when behavior, interfaces, data formats, or safety assumptions
  change.
- Do not create empty scaffolding for speculative features.
- A change is done only when: behavior/limitations are documented; tests cover
  it (or the absence is explained); no unsupported compatibility claim is
  introduced; licensing/provenance is addressed; and the final response lists
  changed files, tests run, and remaining risks.

## Token discipline for future sessions

- This file plus a targeted file read is usually enough to start.
- Use `git grep`/file reads for specific symbols; do not dump whole directories.
- Trust the test command and current snapshot; re-read only files whose
  contents you are about to change.
- Do not paste or summarize entire documents unless the user asks.
- Keep hardware logs out of context unless a task needs a specific transcript.
