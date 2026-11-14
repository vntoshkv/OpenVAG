# Roadmap

The roadmap is capability-based, not date-based. A milestone is complete only when the implementation, tests, documentation, and limitations agree.

## M0 — Repository and legal/technical reconnaissance
- Inspect candidate repositories and source code before reusing anything.
- Record licenses and provenance for dependencies and datasets.
- Identify the exact ELM327 model and the USB VCDS-compatible cable's device IDs/driver/interface.
- Define the initial development environment and test commands.
- Choose the project license only after reviewing code/data compatibility.

**Exit criteria:** written findings, dependency shortlist, adapter investigation notes, and a documented decision on the first prototype.

## M1 — ELM327 read-only OBD-II prototype
- Configure and connect to a known ELM-compatible device.
- Initialize the adapter and capture capability/version responses.
- Read a small subset of supported standard OBD-II values and DTCs.
- Normalize errors and unsupported requests.
- Save timestamped diagnostic sessions.
- Provide mock-based tests that run without hardware.

**Exit criteria:** reproducible setup instructions, passing tests, and a clearly labeled hardware validation report (if a real device was tested).

## M2 — Core boundaries and simulator
- Define adapter and transport interfaces from working requirements.
- Add deterministic simulated adapter/ECU responses.
- Test timeouts, negative responses, malformed data, and cancellation.
- Add privacy-safe logging and session export.

**Current note (2026-11-14):** a line-oriented transport boundary, a Wi-Fi TCP
backend, deterministic simulator, multi-ECU response handling, and explicit
error classification are implemented and covered by tests. Hardware validation,
cancellation, and privacy-safe export remain incomplete.

**Exit criteria:** core behavior can be tested in CI without a car or physical adapter.

## M3 — VAG-focused identification and read-only diagnostics
- Investigate the target Touareg's accessible diagnostic paths.
- Add ECU identification and additional read-only services only when supported and verified.
- Build an initial vehicle/ECU knowledge schema.
- Record sources, compatibility, and verification levels for every data item.

**Exit criteria:** a documented set of functions validated against a named vehicle/ECU configuration.

## M4 — Desktop interface and reports
- Add connection status, supported requests, DTC view, live-data view, and session history.
- Keep the UI separate from protocol logic.
- Make simulator mode obvious to users.
- Export sanitized reports.

**Exit criteria:** ordinary users can complete the initial supported workflow without editing source code.

## M5 — Community data and contribution tooling
- Publish schema examples and validation tools.
- Add contribution templates and automated data validation.
- Document how to submit evidence without sharing VINs or personal data.
- Add a compatibility matrix.

**Exit criteria:** a contributor can add a data definition and test using documented steps.

## M6 — Carefully scoped advanced functions
Only consider after stable read-only diagnostics:
- broader ECU discovery;
- additional transports and protocols;
- additional VAG platforms;
- controlled adaptations, coding, routines, and actuator tests.

Each advanced capability requires a separate design review, supported-ECU scope, explicit confirmation, logging, tests, and recovery guidance. Never promise universal support.

## Explicit non-goals for early milestones
- full VCDS/ODIS parity;
- undocumented write operations;
- bypassing immobilizer, component protection, secure gateways, or access controls;
- proprietary data extraction or copying;
- claiming support based only on an emulator or protocol library.
