# Dependency Review

This record is intentionally small and must be updated before adopting a new
runtime dependency. It records license and maintenance findings; it is not a
substitute for the project's `LICENSE`.

## DR-001 — pySerial

**Reviewed:** 2026-10-28; re-reviewed 2026-11-14  
**Status:** adopted as an optional extra (`openvag[serial]`)

pySerial provides a serial-port abstraction for Windows, macOS, Linux, and BSD
and is distributed under a BSD (3-clause style) license. Its PyPI release
history lists version 3.5, released on 2020-11-23. It is used only by
`openvag.serial_transport` for Bluetooth classic and USB serial adapters. The
core package, simulator, Wi-Fi TCP transport, and test suite remain
dependency-free; tests inject a fake serial device.

The project chose an optional dependency instead of implementing POSIX
`termios` plus a separate Windows path, because that would duplicate a
well-understood, portable layer. pySerial is not imported unless `--serial` or
`--list-ports` is used.

**Provenance:** [pySerial documentation](https://pyserial.readthedocs.io/en/latest/pyserial.html), [PyPI project metadata](https://pypi.org/project/pyserial/), [upstream license](https://github.com/pyserial/pyserial/blob/master/LICENSE.txt).

**Consequences:** install with `pip install -e '.[serial]'`. Without it,
`--serial` and `--list-ports` fail with an actionable error instead of
crashing. Bluetooth classic requires the OS to expose the paired adapter as a
serial port (on macOS usually `/dev/cu.*`); USB adapters use the same backend.
Wi-Fi ELM327 adapters use TCP and do not need pySerial.

## Reviewed candidates — not adopted (2026-11-14)

The project direction prompted a review of whether existing implementations
could be reused or copied. The review below records what was checked and why
nothing was imported. No code from these projects is present in this
repository.

**License compatibility rule of thumb:** the project is licensed under
Apache-2.0 (see `docs/DECISIONS.md`, D-011). GPL-family code is not adopted: it
would impose copyleft on the combined work, and GPL-2.0 is incompatible with
Apache-2.0. Code without a license grants no copying rights at all. Permissive
code (MIT/BSD/Apache-2.0) can be reused with attribution, but must keep its own
license notices.

| Candidate | License found | Possible use | Verdict |
|---|---|---|---|
| [python-OBD](https://github.com/brendan-w/python-OBD) | GPL-2.0 | OBD request handling and decoders | Not adopted: GPL-2.0 would impose copyleft and is incompatible with Apache-2.0. Keep the small independent OBD layer. |
| [ELM327-emulator](https://github.com/Ircama/ELM327-emulator) | CC BY-NC-SA 4.0 (license file in repository) | Multi-ECU adapter simulation for tests | Not vendored: the noncommercial restriction is incompatible with an open-source distribution, and CC is not a software license. May be used as an external development tool. |
| [elmulator](https://github.com/qadanm/elmulator) | MIT | BLE-oriented emulator | Permissive, but small and new; not adopted. |
| [OBDII (py-obdii)](https://github.com/PaulMarisOUMary/OBDII) | MIT | Modern OBD-II client and decoders | Permissive and maintained; not adopted now because the prototype's small OBD layer is sufficient and adoption would couple the core to an external API. Revisit if decoder coverage grows. |
| [python-elm](https://github.com/franciscoruiz/python-elm) | MIT | Older ELM327 client | No activity since 2014; not adopted. |
| [kwp2000-can](https://pypi.org/project/kwp2000-can/) | MIT | KWP2000 over CAN TP2.0 / J2534 | Very early (0.1.0, placeholder project URLs); not adopted; relevant only to future VAG recon. |
| [python-udsoncan](https://github.com/pylessard/python-udsoncan) | MIT | Future UDS client | Candidate for a later optional extra; not adopted. |
| [python-can-isotp](https://github.com/pylessard/python-can-isotp) | MIT | Future ISO-TP transport | Candidate for a later optional extra; not adopted. |
| [python-can](https://github.com/hardbyte/python-can) | LGPL-3.0 | Future CAN interface layer | Candidate only; LGPL distribution conditions must be reviewed before adoption. Do not copy code. |
| [zigmars/openVAG](https://github.com/zigmars/openVAG) | No license detected | Unrelated project with a similar name | Cannot copy: all rights reserved. Also a name-confusion and provenance risk; not consulted for implementation details. |
| [esp32_tp20_datalogger](https://github.com/xerootg/esp32_tp20_datalogger) | No license detected | VW TP 2.0 protocol notes | Cannot copy. Protocol work must rely on public standards and independent observation. |

**Consequences:**

- The prototype continues as an independent implementation of the public
  OBD-II request/response rules already represented by its tests.
- If a permissive library is adopted later, it must be recorded here with
  version, license, maintenance status, and transitive dependencies, and
  preferably exposed as an optional extra so the core stays dependency-free.
- Reading an unlicensed repository and copying it is not permitted at all.
  Copying GPL code would change the project's license obligations and is not
  planned.
