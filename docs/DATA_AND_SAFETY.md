# Data Provenance, Verification, Privacy, and Safety

## 1. Provenance and redistribution

Every third-party code component, dataset, table, image, and documentation excerpt must have its origin and license reviewed before inclusion or redistribution.

For each vehicle-specific knowledge item, record as applicable:
- stable item ID;
- source URL or document reference;
- author/contributor and date collected;
- license or redistribution basis;
- vehicle platform and ECU applicability;
- ECU part number and hardware/software identifiers, if known;
- protocol/service and identifier;
- raw response fixture, when legally and safely shareable;
- decoding formula, units, byte order, and assumptions;
- verification method and status;
- known limitations.

Do not copy closed-source VCDS/ODIS databases or proprietary application internals into the project. Public availability does not automatically grant redistribution rights.

## 2. Verification states

Use a small, explicit vocabulary. Suggested initial states:
- `unverified`: submitted or inferred, not independently checked;
- `simulator-tested`: tests pass against a simulated response only;
- `observed`: seen on a real device/ECU, semantic meaning may remain uncertain;
- `verified`: meaning and decoding checked against reliable evidence on a stated configuration;
- `multi-configuration-verified`: independently reproduced across multiple stated configurations;
- `deprecated`: known to be wrong, obsolete, or superseded.

Do not treat `simulator-tested` as real-hardware verification. Store test conditions and evidence for higher verification states.

## 3. Compatibility specificity

Avoid statements such as “works with all Touareg 7P vehicles” unless supported by evidence. Compatibility may depend on:
- model year and market;
- platform/network topology;
- ECU part number;
- hardware and software versions;
- adapter and firmware;
- protocol and diagnostic session;
- gateway configuration.

When compatibility is unknown, say so explicitly.

## 4. Safe defaults

The initial application must be read-only by default.

The following are state-changing or potentially hazardous and require a separate safety review before implementation:
- clearing DTCs;
- coding or adaptation writes;
- actuator/output tests;
- routine control;
- security access;
- ECU resets, programming, flashing, or configuration changes.

If introduced later, these functions must require explicit user intent, identify the target ECU and operation, explain prerequisites and risks, preserve relevant before-state where possible, record an audit log, handle negative responses safely, and never run automatically. Do not implement ECU flashing/programming in early milestones.

Do not invent or brute-force security keys, bypass anti-theft systems, defeat secure gateways, or bypass access controls. Support legitimate documented access workflows only where legally and technically appropriate.

## 5. Real vehicle versus simulator

Every response/session must make its source clear:
- real adapter and ECU;
- mock;
- simulator;
- imported recording.

Never mix simulated data into a real diagnostic report without an unmistakable label.

## 6. Privacy

Diagnostic logs can contain VINs, identifiers, timestamps, location hints, user names, and other sensitive data. Before export or issue submission:
- warn the user;
- offer VIN and personal-data redaction;
- avoid logging secrets or access tokens;
- do not upload data automatically;
- document what the report contains.

Do not commit unredacted VINs, registration plates, customer records, or raw logs with personal data to public repositories.

## 7. Data quality and unknowns

Never fill missing fields with plausible-looking guesses. Use explicit `unknown`, `null`, or a schema-approved equivalent. Separate raw observations from interpretation. Record assumptions and confidence. If two sources disagree, preserve the conflict and ask for review rather than silently selecting one.

## 8. Responsible testing

Start with mocks and simulators. On a real vehicle, begin with read-only requests, a stable power supply where appropriate, and a clear understanding of the adapter and target ECU. Do not run experimental write operations on a road-going vehicle. Hardware tests are manual and opt-in.
