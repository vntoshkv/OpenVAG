# Proposed Architecture

This document describes intended boundaries, not a guarantee that these modules already exist. Implement incrementally and revise the design when real requirements justify it.

## 1. Architectural layers

### Applications
- Desktop UI (a Qt/PySide-based application is a candidate).
- CLI for diagnostics, testing, and automation.
- Report export and session comparison.

Applications should call stable core interfaces rather than communicate with adapters directly.

### Core
- Adapter interface and capability discovery.
- Transport abstractions: serial, CAN, ISO-TP, and future transports as needed.
- Protocol implementations or wrappers: standard OBD-II, UDS, and selected legacy protocols.
- Diagnostic sessions, timeouts, cancellation, and error normalization.
- Discovery and diagnostics orchestration.
- Logging with sensitive-data redaction.

### Vehicle knowledge base
- Vehicle/platform metadata.
- ECU identification and applicability.
- DTC descriptions.
- Measurement definitions and decoders.
- Coding/adaptation/procedure definitions, only when well sourced and safely supported.
- Provenance, license, verification state, and compatibility constraints.

Keep knowledge data separate from protocol code. A protocol implementation should not hard-code a particular Touareg ECU's private identifiers.

### Plugins
Potential plugin types:
- adapter backends;
- data providers;
- report exporters;
- diagnostic tools;
- UI extensions.

Do not implement a general-purpose plugin execution system until a concrete use case exists. Third-party plugins should not receive unrestricted access to vehicle write operations by default.

### Simulator and tests
- Mock adapters for unit tests.
- Protocol-level fixtures.
- Virtual ECU/gateway scenarios.
- Optional hardware tests, never required for ordinary CI.

## 2. Conceptual data flow

User action
  -> application/use case
  -> diagnostic session
  -> protocol client
  -> transport
  -> adapter backend
  -> vehicle ECU

Responses travel back through the same layers. Vehicle-specific decoders and metadata are consulted separately to interpret responses.

## 3. Initial implementation choices (provisional)

- Language: Python.
- Packaging: `pyproject.toml`.
- Tests: the Python standard library `unittest` runner. This keeps the core
  test path dependency-free; pytest may be adopted later only if fixtures or
  plugins justify the extra dependency.
- Wi-Fi ELM327: standard-library TCP transport (`openvag.tcp_transport`),
  implemented.
- Bluetooth/USB serial: optional `pyserial` extra and
  `openvag.serial_transport`, implemented; it is not required by the core or
  by CI.
- CAN abstraction: evaluate `python-can`.
- ISO-TP: evaluate `can-isotp`.
- UDS: evaluate `udsoncan`.
- OBD-II over ELM-compatible devices: independent minimal implementation;
  `python-OBD` was reviewed but not adopted (GPL, see
  [`DEPENDENCY_REVIEW.md`](DEPENDENCY_REVIEW.md)).
- Persistent sessions: SQLite is a reasonable initial option.
- Desktop UI: evaluate PySide6 after the first CLI prototype.

Before adopting a dependency, inspect its current maintenance status, license, supported platforms, transitive dependencies, and whether it actually fits the chosen hardware. Do not add all candidates automatically.

## 4. Adapter abstraction

The core should depend on a documented adapter contract, not on a brand name. The contract will likely need:
- connect/disconnect and connection state;
- capabilities and transport type;
- send/receive operations or a transport-specific interface;
- timeouts and cancellation;
- normalized errors;
- safe close/cleanup behavior.

Do not force ELM327, generic CAN, J2534, and a proprietary VCDS-compatible cable into an inaccurate one-size-fits-all abstraction. Use a small common interface plus explicit capabilities or specialized interfaces.

For the line-oriented ELM327 path, `LineTransport` returns response lines without the ELM prompt. Echo, `SEARCHING...`, `BUS INIT`, and multiple ECU responses are normalized above the transport so that a TCP or serial backend does not need adapter-specific parsing. Wi-Fi uses a plain TCP socket; Bluetooth/USB serial uses the optional `pyserial` backend behind the same line contract.

## 5. Protocol versus vehicle data

Protocol code answers: “How do I form, send, receive, and parse this service?”
Vehicle data answers: “Which ECU/service/identifier applies here, what does the response mean, and for which hardware/software variants is it valid?”

Keep these concerns separate. Successful transport or a positive UDS response does not by itself establish the semantic meaning of returned bytes.

## 6. Error model

Distinguish at least:
- adapter unavailable;
- connection failed;
- unsupported adapter command;
- transport timeout;
- malformed frame/message;
- protocol negative response;
- service unsupported by ECU;
- identifier unavailable;
- decoder/data definition missing;
- request blocked by safety policy;
- simulated response.

Avoid collapsing all failures into “no data.”

## 7. Test strategy

- Unit tests for parsing, scaling, state machines, and data validation.
- Protocol tests using deterministic byte-level fixtures.
- TCP transport tests against a local loopback fake bridge.
- Serial transport tests with an injected fake device; pySerial is not required
  in CI.
- Simulator tests for positive, negative, delayed, and missing responses.
- Integration tests for supported adapters where hardware is available.
- Manual vehicle test reports that record vehicle/ECU/software context and test conditions.

Hardware tests must be opt-in and must not run in CI automatically. Simulator success is not proof of real-vehicle compatibility.

## 8. Initial vertical slice

Implement only a small, end-to-end read-only path:
1. configure a TCP endpoint for a Wi-Fi ELM327 bridge, or a serial port for a
   supported adapter;
2. initialize the adapter and report its responses/capabilities;
3. request a few standard OBD-II values and DTCs;
4. normalize results and errors;
5. save a timestamped session;
6. test the same logic using mocks or a simulator.

Do not start with a full Auto-Scan, vehicle-specific coding, or a large speculative plugin system.
