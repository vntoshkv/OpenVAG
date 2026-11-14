# Hardware and Adapter Notes

This file records what is physically available and what has actually been
observed. Nothing here is a compatibility claim. No real-vehicle test has been
performed yet.

## 1. Available hardware

| Device | Expected transport | Reported model | Verification status |
|---|---|---|---|
| ELM327-compatible adapter | TCP socket to the adapter's access point | Unknown; reported PIC-based v1.5-compatible board | `unverified` |
| ELM327-compatible adapter | Classic Bluetooth SPP, exposed by the OS as a serial device | Unknown; reported PIC-based v1.5-compatible board | `unverified` |

Initial development environment: macOS on Apple silicon, Python 3.9.6. Python
3.9 is end-of-life; the compatibility floor will be reviewed before public
release.

### Transport implementation status

- Wi-Fi TCP transport: implemented in `openvag.tcp_transport` using the
  standard library; covered by loopback tests, **not yet tested against a real
  adapter**.
- Bluetooth classic / USB serial: not implemented.
- No real-vehicle request has been performed.

Validation vehicle: Volkswagen Touareg NF / 7P, 3.6 FSI, engine code CMTA
(no hardware test performed yet).

## 2. Adapter identification procedure

Run this before relying on any adapter-specific behavior. Record the exact,
sanitized command output here with the date. Do not trust the `ATI` version
string alone: clones frequently misreport it.

1. Wi-Fi: join the adapter's access point, connect to its TCP port (commonly
   `192.168.0.10:35000`, confirm for the actual device), then send `ATZ`,
   `ATI`, `AT@1`, `ATDPN`, `ATRV`.
2. Bluetooth: pair the adapter in the OS, find the serial device it creates
   (macOS usually exposes `/dev/cu.*`), open it at 38400 8N1, then send the
   same commands.
3. Record: date, host OS/Python, device label, VID/PID if visible, exact
   responses, and whether the commands were accepted at all.

An unanswered command is evidence too: it indicates a limitation of the clone
and must be recorded as such rather than worked around silently.

## 3. Known risks with ELM327 clones

- Firmware may be a clone that reports a version it does not fully implement.
- AT command coverage, timing, and error text may differ from the ELM
  documentation.
- Multi-frame and flow-control behavior may be incomplete, which matters for
  anything beyond short OBD-II responses.
- Wi-Fi adapters create their own access point; the connection drops when the
  network changes, and reconnection behavior must be handled explicitly.
- Bluetooth SPP behavior depends on the OS pairing stack and the adapter.

## 4. Scope of the ELM327 path

ELM327-compatible adapters are intended here for standard OBD-II requests
(read-only). They are not assumed to be a general ISO-TP/UDS transport for
VAG modules. Reaching modules other than the engine requires a separate,
documented transport decision and its own evidence; see the roadmap.

## 5. First real Wi-Fi run

This is a manual, opt-in hardware step. It performs read-only requests only.

1. Join the ELM327 Wi-Fi access point from the development machine.
2. Confirm the bridge address and port (commonly `192.168.0.10:35000`).
3. Run:

   ```shell
   PYTHONPATH=src python3 -m openvag.cli --tcp 192.168.0.10:35000 --session wifi-session.json
   ```

4. Record the observed `ATI`, `AT@1`, and `ATDPN` output here with the date,
   adapter label, host OS, and the vehicle state (ignition on/off, engine
   running/not running).
5. Label the result `observed`, not `verified`. Do not commit a session that
   contains vehicle-identifying data; sessions are ignored by git by default.

If the first request times out, stop and capture the raw response rather than
increasing timeouts blindly; the adapter may still be searching for a protocol.

## 6. What is explicitly not claimed

- No adapter has been verified against any vehicle yet.
- No simulated result is real vehicle data.
- No VAG-specific module, address, or coding function is supported.
