# Contributing

Thanks for helping build an independent, community-maintained vehicle diagnostic platform.

## Before contributing
- Read `AGENTS.md` and the relevant documents under `docs/`.
- Check open issues and existing implementations before adding a new abstraction.
- Keep changes focused and explain the problem they solve.
- Do not assume a protocol feature is supported by a given ECU just because the standard defines it.

## Licensing of contributions
Unless explicitly stated otherwise, contributions are submitted under the
Apache License 2.0 (inbound = outbound). No separate contributor license
agreement is required. By contributing, you confirm that you have the right to
submit the code, data, and documentation, and that they can be distributed
under the project license.

## Code contributions
- Add or update tests.
- Prefer deterministic unit and simulator tests.
- Hardware tests must be opt-in and documented.
- Document supported environments, limitations, and failure modes.
- Check dependency licenses and maintenance before adding a dependency.
- Do not include credentials, access tokens, VINs, registration plates, or unredacted customer logs.

## Vehicle data contributions
For every new definition, provide as much of the following as is available:
- vehicle/platform and ECU applicability;
- ECU hardware/software identifiers or constraints;
- source/provenance and redistribution status;
- protocol/service and identifier;
- raw response example, with private information removed;
- decoding/scaling/units/byte order;
- test method and verification status;
- limitations and conflicting evidence.

If a field is unknown, mark it unknown. Do not guess.

## Pull request checklist
- [ ] Scope and motivation are clear.
- [ ] Tests added or updated; test results are reported accurately.
- [ ] Documentation matches actual behavior.
- [ ] No unsupported compatibility claims.
- [ ] No unlicensed proprietary data or copied closed-source implementation.
- [ ] Vehicle data has provenance and verification state.
- [ ] Any safety-relevant behavior has an explicit review and is not enabled by default.
- [ ] Logs and fixtures are sanitized.

## Reporting security issues
Do not publish details that could enable unauthorized vehicle access or bypass access controls in a public issue. Until a dedicated security contact is established, report concerns privately to the repository maintainers through an available private channel.

## Respectful collaboration
Assume good intent, be specific, and critique code or evidence rather than people. A code of conduct should be adopted before the community grows.
