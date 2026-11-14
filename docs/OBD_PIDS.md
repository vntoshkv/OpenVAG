# Standard OBD-II PID Coverage

This file documents the read-only standard OBD-II requests implemented by the
prototype. It is a coverage and provenance record, not a claim of support for
any particular vehicle.

**Verification status:** `simulator-tested` only. No value has been verified on
a real vehicle, and applicability to the Touareg 7P / CMTA is unknown.

**Source:** public OBD-II service definitions (SAE J1979 / ISO 15031-5). The
implementation is independent; no proprietary PID table, VCDS/ODIS database,
or copyrighted data file was copied. Formulas are implemented in
`src/openvag/obd.py`.

## Capability discovery

The snapshot first requests the 32-PID availability bitmaps:

- `0100` for PIDs `0x01`–`0x20`;
- `0120` for PIDs `0x21`–`0x40`, requested only if `0x20` is advertised;
- `0140` for PIDs `0x41`–`0x60`, requested only if `0x40` is advertised.

Only live-data PIDs advertised in those bitmaps are requested. When multiple
ECUs answer a bitmap, the request set uses the union; `response_index` records
the order but **not** a verified ECU identity, because ELM headers are disabled
(`ATH0`).

## Live-data PIDs

Bytes are the OBD-II data bytes after the `41 <PID>` response prefix. All
values are big-endian.

| PID | Request | Name | Bytes | Unit | Formula / notes | Status |
|---|---|---|---|---|---|---|
| `0x01` | `0101` | Monitor status since DTCs cleared | A–D | — | A bit 7 = MIL on; A bits 0–6 = DTC count. B–D retained as raw readiness bytes, not interpreted. | `simulator-tested` |
| `0x04` | `0104` | Calculated engine load | A | % | `A × 100 / 255` | `simulator-tested` |
| `0x05` | `0105` | Engine coolant temperature | A | °C | `A − 40` | `simulator-tested` |
| `0x06` | `0106` | Short-term fuel trim, bank 1 | A | % | `(A − 128) × 100 / 128` | `simulator-tested` |
| `0x07` | `0107` | Long-term fuel trim, bank 1 | A | % | `(A − 128) × 100 / 128` | `simulator-tested` |
| `0x08` | `0108` | Short-term fuel trim, bank 2 | A | % | `(A − 128) × 100 / 128` | `simulator-tested` |
| `0x09` | `0109` | Long-term fuel trim, bank 2 | A | % | `(A − 128) × 100 / 128` | `simulator-tested` |
| `0x0A` | `010A` | Fuel pressure | A | kPa | `A × 3` | `simulator-tested` |
| `0x0B` | `010B` | Intake manifold absolute pressure | A | kPa | `A` | `simulator-tested` |
| `0x0C` | `010C` | Engine RPM | A, B | rpm | `((A × 256) + B) / 4` | `simulator-tested` |
| `0x0D` | `010D` | Vehicle speed | A | km/h | `A` | `simulator-tested` |
| `0x0E` | `010E` | Timing advance | A | ° | `A / 2 − 64`, relative to cylinder 1 | `simulator-tested` |
| `0x0F` | `010F` | Intake air temperature | A | °C | `A − 40` | `simulator-tested` |
| `0x10` | `0110` | Mass air flow | A, B | g/s | `((A × 256) + B) / 100` | `simulator-tested` |
| `0x11` | `0111` | Throttle position | A | % | `A × 100 / 255` | `simulator-tested` |
| `0x1F` | `011F` | Run time since engine start | A, B | s | `(A × 256) + B` | `simulator-tested` |
| `0x21` | `0121` | Distance travelled with MIL on | A, B | km | `(A × 256) + B` | `simulator-tested` |
| `0x2F` | `012F` | Fuel tank level | A | % | `A × 100 / 255` | `simulator-tested` |
| `0x31` | `0131` | Distance since codes cleared | A, B | km | `(A × 256) + B` | `simulator-tested` |
| `0x33` | `0133` | Absolute barometric pressure | A | kPa | `A` | `simulator-tested` |
| `0x42` | `0142` | Control module voltage | A, B | V | `((A × 256) + B) / 1000` | `simulator-tested` |
| `0x46` | `0146` | Ambient air temperature | A | °C | `A − 40` | `simulator-tested` |
| `0x5C` | `015C` | Engine oil temperature | A | °C | `A − 40` | `simulator-tested` |
| `0x5E` | `015E` | Engine fuel rate | A, B | L/h | `((A × 256) + B) / 20` | `simulator-tested` |

## Diagnostic trouble codes

| Request | Meaning | Response prefix | Status |
|---|---|---|---|
| `03` | Stored DTCs | `43` | `simulator-tested` |
| `07` | Pending DTCs | `47` | `simulator-tested` |
| `0A` | Permanent DTCs | `4A` | `simulator-tested` |

Codes are decoded structurally (family and digits), for example `P0133`.
This project does **not** embed proprietary DTC description tables; human-readable
descriptions with provenance remain a separate knowledge-base task.

## Not implemented yet

- freeze-frame data (`02`);
- O2 sensor PIDs (`0114`–`011B`);
- readiness-monitor bit semantics beyond MIL and DTC count;
- full mode `09` identifiers (VIN, calibration ID, CVN) — VIN is privacy-sensitive;
- multi-frame handling beyond what the ELM327 bridge already assembles;
- any vendor-specific or VAG-specific PID/address.

Each of these needs its own source review, decoder tests, and, where relevant,
a privacy decision before implementation.
