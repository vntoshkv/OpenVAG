# Project Vision

## 1. Mission

Build an independent, open-source, community-maintained diagnostic platform that makes automotive diagnostic tooling more transparent, extensible, testable, and accessible.

The initial focus is Volkswagen Group vehicles. The architecture should avoid unnecessary brand-specific coupling so that broader support may be added later if there is community interest and reliable technical evidence.

The project is not a clone of a proprietary application. It aims to implement useful diagnostic capabilities independently using documented standards, lawful public information, independently collected observations, and compatible open-source components.

## 2. Who it is for

- Vehicle owners who need understandable diagnostic reports.
- Independent repairers and automotive diagnosticians.
- Developers building protocol tools, adapters, simulators, or interfaces.
- Community contributors who can verify vehicle-specific information.

## 3. Long-term capabilities (aspirational)

Potential capabilities include:
- adapter discovery and connection status;
- standard OBD-II diagnostics;
- supported CAN and ISO-TP transport;
- UDS and selected legacy protocols where justified;
- ECU discovery and multi-module reports;
- DTC reading and, only with explicit safeguards, clearing;
- live data, logging, charts, and session comparison;
- structured ECU identification and vehicle-specific data;
- controlled support for coding, adaptations, routines, and actuator tests;
- simulator-based development and plugin interfaces;
- exportable reports and privacy-preserving issue reports.

These are goals, not claims about currently implemented features. Every capability must be scoped and verified individually.

## 4. Core principles

### Independence
Use standards, public documentation, and independently developed code. Do not copy closed-source VCDS/ODIS implementation details, proprietary databases, or protected assets.

### Adapter independence
Keep adapter-specific behavior behind stable interfaces. Do not assume all USB VCDS-compatible cables expose the same API or transport.

### Evidence over guesses
Unknown addresses, DIDs, scaling, units, and applicability remain unknown until verified. Distinguish specification-derived facts, observed facts, hypotheses, and simulator fixtures.

### Data as a first-class product
Vehicle knowledge should be structured, versioned, reviewable, attributable, and independently testable.

### Safety by default
Read-only behavior is the default. Any operation that changes ECU state must be separately designed, reviewed, confirmed, and logged.

### Community governance
Make it easy to contribute, but do not automatically treat an unreviewed contribution as verified truth.

### Cross-platform where practical
Begin with a developer-friendly Python implementation. Avoid unnecessary Windows-only assumptions in core protocol and data modules.

## 5. Out of scope for the initial milestone

- Claiming full VCDS or ODIS feature parity.
- Coding, adaptations, actuator tests, security access, or ECU writes.
- Supporting every VAG generation or every adapter.
- Reverse engineering or bypassing proprietary application internals.
- Publishing data with unclear redistribution rights.
- Treating an emulator as proof of compatibility with a real vehicle.

## 6. Initial proving ground

The first validation vehicle is a Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA. Initial available interfaces are an ELM327 and a Chinese USB VCDS-compatible cable. Their exact models and compatibility are not yet known.

The first prototype should target standard OBD-II read operations through ELM327. The VCDS-compatible cable should be investigated separately, without assuming it can be used as a generic serial or CAN device.

## 7. Success criteria

Early success means a contributor can:
1. install the project from documented instructions;
2. run tests without a vehicle;
3. connect a supported adapter;
4. execute a small set of read-only requests;
5. save a reproducible diagnostic session;
6. understand which results are verified, unknown, unsupported, or simulated;
7. add a new data description or test through a documented contribution process.
