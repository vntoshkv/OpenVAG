# Decision Log

This log records current project choices and open questions. Decisions may be revised through documented discussion.

## Accepted direction

### D-001 — Build an independent open-source platform
**Status:** accepted  
**Decision:** Aim for a community-maintained diagnostic platform, not a private one-off script and not a copy of proprietary VCDS/ODIS internals.  
**Reason:** Reusable architecture, transparent behavior, and community contributions are core goals.

### D-002 — Initial validation vehicle
**Status:** accepted  
**Decision:** Use Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA as the first validation target.  
**Limit:** This does not constrain future supported vehicles.

### D-003 — Initial hardware
**Status:** accepted as available hardware; compatibility unverified  
**Decision:** Investigate an ELM327 and a Chinese USB VCDS-compatible cable.  
**Limit:** Do not assume the VCDS-compatible cable behaves as a generic serial/CAN/J2534 adapter.

### D-004 — Python-first implementation
**Status:** accepted provisionally  
**Decision:** Use Python for the first prototype and keep core modules cross-platform where practical.  
**Reason:** Rapid development, ecosystem for OBD-II/CAN/UDS, and accessible contribution workflow.

### D-005 — Read-only first
**Status:** accepted  
**Decision:** Initial milestones focus on read-only OBD-II and carefully scoped read-only VAG diagnostics.  
**Reason:** Reduce risk while validating transport and protocol correctness.

### D-006 — Separate protocol code from vehicle knowledge
**Status:** accepted  
**Decision:** Keep transport/protocol implementation independent from vehicle-specific data definitions.  
**Reason:** New vehicle knowledge should not require changing core protocol code.

### D-007 — Evidence and provenance required
**Status:** accepted  
**Decision:** Track source, applicability, verification status, and limitations for vehicle-specific data.  
**Reason:** Community contributions must be reproducible and distinguish facts from hypotheses.

### D-008 — Canonical public repository
**Status:** accepted (2026-11-14)  
**Decision:** The canonical repository is <https://github.com/vntoshkv/OpenVAG>. Issues and pull requests live there.  
**Reason:** The repository is the canonical public home for the project; it is the single source of truth for code and documentation.  
**Consequences:** The earlier scratch directory is not authoritative. Local development must be a clone of, or push to, this repository.

### D-009 — Development host and CI matrix
**Status:** proposed (2026-11-14)  
**Decision:** Initial development is on macOS on Apple silicon. CI covers Linux, Windows, and macOS, with Python 3.9 and 3.12, so the core stays cross-platform. Windows remains a supported target even though it is not the first development host.  
**Reason:** Decisions should reflect the development hardware actually in use; a macOS-only implementation would violate the cross-platform goal.  
**Consequences:** If accepted, the "Windows-first" wording in `AGENTS.md` should be revised; this has not been changed yet.

### D-010 — Transport strategy for the available adapters
**Status:** accepted for implementation (2026-11-14); Wi-Fi TCP and Bluetooth/USB serial backends implemented and tested without hardware; real hardware validation pending  
**Decision:** Keep `LineTransport` as the adapter boundary and add separate backends:
- Wi-Fi ELM327: plain TCP socket, standard library only;
- Bluetooth classic ELM327: OS-provided serial device via an optional `pyserial` extra;
- USB ELM327: the same serial path.

Do not force generic CAN/UDS through the ELM327 backend. Future CAN/UDS support is a separate transport and protocol decision, evaluated after reconnaissance.

**Reason:** Initial development uses Wi-Fi and Bluetooth ELM327 adapters on a macOS host. TCP is dependency-free and testable first; serial covers Bluetooth and USB without a platform-locked design. ELM327 is not assumed to be a general ISO-TP/UDS transport.
**Consequences:** No adapter-specific assumptions belong in protocol decoders. Read-only request policy remains enforced above the transport. `pyserial` is an optional extra recorded in DR-001; the core and CI remain dependency-free. Hardware claims remain blocked until an observed transcript is recorded in [`HARDWARE.md`](HARDWARE.md).

### D-011 — Apache-2.0 license
**Status:** accepted (2026-11-14)  
**Decision:** License the project under the Apache License, Version 2.0. The copyright notice is "OpenVAG contributors". Add `LICENSE` and `NOTICE`, and update `pyproject.toml` and `README.md`.  
**Reason:** Apache-2.0 is OSI-approved and permissive, permits commercial use and modification, and includes an explicit patent grant and a trademark clause. It fits the goal of a community-maintained open-source project without field-of-use restrictions.  
**Consequences:** GPL-2.0 code cannot be combined with this project. Third-party permissive code retains its own license and notices. Contributions are accepted under Apache-2.0 unless explicitly stated otherwise.

## Open decisions

### O-001 — Final project name
**Status:** open  
**Current working name:** OpenVAG Diagnostic.  
**Action:** Check name availability and trademark/confusion risks before public launch. An unrelated GitHub project, `zigmars/openVAG`, already exists (no detected license, no activity since 2022), and several other repositories use similar `OpenVAG`/`openVag` names. This increases confusion risk and is not a source we may copy from.

### O-002 — Repository host and organization
**Status:** resolved by D-008  
**Resolution:** GitHub, <https://github.com/vntoshkv/OpenVAG>. Organization/ownership may be revisited before broad promotion.

### O-003 — Software license
**Status:** resolved by D-011  
**Resolution:** Apache License 2.0; see `LICENSE` and `NOTICE`.

### O-004 — First adapter backend
**Status:** open; hardware identified, behavior unverified  
**Current hardware:** ELM327-compatible adapters over Wi-Fi and Bluetooth classic; models and firmware unverified, reported PIC-based v1.5-compatible boards. See [`HARDWARE.md`](HARDWARE.md).
**Candidate:** Wi-Fi TCP backend first (standard library, easy to test on the current macOS host), then Bluetooth classic as an OS serial device.  
**Action:** Record `ATZ`, `ATI`, `AT@1`, `ATDPN`, and `ATRV` output from each device, then decide the smallest reliable API.

### O-005 — VCDS-compatible cable
**Status:** open; current inventory does not confirm that such a cable is available  
**Action:** If one is obtained, record USB VID/PID, driver, device interface, and any documented SDK/API. Determine whether third-party communication is possible without proprietary protocol copying or unsafe firmware modification. Do not assume it behaves as a generic serial/CAN/J2534 adapter.

### O-006 — Data schema
**Status:** open  
**Action:** Choose JSON/YAML/SQLite boundaries based on validation needs. Keep schema versioned and include provenance and applicability.

### O-007 — Desktop UI
**Status:** open  
**Candidate:** PySide6 after a CLI prototype proves the core workflow.

### O-008 — Community governance
**Status:** open  
**Action:** Define maintainers, review requirements, security-reporting channel, contribution policy, and release process before broad promotion.

## Decision discipline

New decisions should include an ID, status, decision, rationale, consequences, and date. Do not silently convert a suggestion into an accepted decision.
