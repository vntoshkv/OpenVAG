# Instructions for AI agents

This file is the entry point for AI coding agents working in this repository.

## Before making changes
1. Read `README.md`, `docs/PROJECT_VISION.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DATA_AND_SAFETY.md`, and `docs/DECISIONS.md`.
2. Inspect the existing repository and tests before proposing or implementing architecture. Do not assume planned modules already exist.
3. Identify the smallest useful change, implement it, and add or update tests.
4. State what was actually tested. Never claim hardware compatibility without evidence from the relevant device and vehicle configuration.

## Project identity
- Working name: **OpenVAG Diagnostic**. This is a provisional name, not a claim of affiliation with Volkswagen, Audi, or Ross-Tech.
- Goal: build an independent, open-source, community-maintained diagnostic platform for VAG vehicles, with an architecture that can later support other vehicles where practical.
- Initial development target: Python, Windows-first for developer convenience, with cross-platform design where feasible.
- Initial validation vehicle: Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA.
- Initially available adapters: ELM327 over Wi-Fi and ELM327 over Bluetooth classic (model, firmware, and clone behavior unverified); a Chinese USB VCDS-compatible cable is not confirmed to be available. See `docs/HARDWARE.md`. Exact hardware, firmware, protocol support, and third-party compatibility are not yet verified.

## Non-negotiable engineering principles
- Prefer documented standards, open-source components, public documentation, and independently gathered measurements.
- Do not decompile, disassemble, extract proprietary databases from, or copy closed-source VCDS/ODIS internals. Do not use them as a template in ways prohibited by their licenses. Build an independent implementation.
- Do not copy proprietary data or documentation into the repository without a clear right to redistribute it. Record provenance and license for imported datasets and dependencies.
- Treat all hardware and vehicle compatibility as unverified until tested. Clearly distinguish protocol capability from support implemented in this project.
- Default to read-only operations. Any write, coding, adaptation, actuator test, routine control, security access, or destructive operation must be explicit, gated, logged, and documented before implementation.
- Never silently guess diagnostic addresses, identifiers, scaling formulas, byte order, units, or vehicle applicability.
- Never present simulated results as real vehicle data.
- Do not add dependencies without explaining why they are needed and checking their licenses and maintenance status.
- Keep modules small, typed where useful, testable, and documented. Prefer interfaces and dependency injection over hardware-specific assumptions.
- Never commit vehicle-identifying data, VINs, license plates, customer records, access keys, logs with personal data, or secrets unless explicitly sanitized and necessary.

## Data quality
Every vehicle-specific item should, where applicable, include:
- source and provenance;
- license or redistribution status;
- vehicle/platform and ECU applicability;
- ECU hardware/software identifiers or known version constraints;
- verification status and method;
- units, scaling, byte order, and decoding notes;
- confidence and known limitations.

Use the verification vocabulary in `docs/DATA_AND_SAFETY.md`. Unknown values must remain explicitly unknown rather than being filled with plausible guesses.

## Workflow
- Start with a brief plan for non-trivial changes.
- Make changes in small, reviewable increments.
- Add unit tests for pure logic and simulator-based integration tests for protocol behavior.
- Hardware tests must be optional and must not run automatically in CI.
- Run the relevant tests and report commands/results accurately.
- Update docs when behavior, interfaces, data formats, or safety assumptions change.
- Do not make broad refactors unrelated to the task.
- Do not create empty scaffolding for speculative features unless the user explicitly asks for it.
- If a requirement is ambiguous or a change could cause writes to an ECU, stop and ask for clarification.

## Definition of done
A change is not complete until:
1. behavior and limitations are documented;
2. tests cover the change or the absence of tests is explained;
3. no unsupported compatibility claim is introduced;
4. licensing/provenance concerns are addressed for new dependencies or data;
5. the final response summarizes changed files, tests run, and remaining risks.
