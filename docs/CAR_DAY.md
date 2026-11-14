# Car-Day Checklist

First real read-only run against the Touareg 7P. No coding, adaptation,
actuator, security-access, or DTC-clearing operation is part of this session.

## Before leaving

1. Update the repository and run the dry run:

   ```shell
   git pull
   ./collect.sh --simulate
   ```

   Inspect `logs/collect-*.md`. If the dry run fails, fix the environment before
   going to the car.

2. Check that both adapters are available and labelled. You do not need a VIN.
3. Pair the Bluetooth adapter in the OS if possible; note its name. If pairing
   cannot be done without vehicle power, do it at the car.
4. Close applications that could open the adapter or serial port.
5. Charge the laptop and consider disabling sleep for the session
   (macOS: `caffeinate -dimsu` in a separate terminal).
6. Decide where to keep the logs. `logs/` is git-ignored; never commit a real
   session.

## At the car

1. Park safely, apply the handbrake, select Park or Neutral.
2. Switch ignition on. For meaningful live data, start the engine and let it
   idle; never work under the car during this procedure.
3. Connect the ELM327 to the OBD port and confirm its power LED.
4. Prevent other phones/apps from connecting to the adapter.
5. **Wi-Fi run:** join the adapter's access point. Note the laptop's IP and the
   gateway (commonly `192.168.0.10`). The laptop may lose internet; this is
   expected.
6. **Bluetooth run:** pair the adapter and confirm a `/dev/cu.*` port with
   `openvag --list-ports` (or the collector's auto-detection).
7. Run:

   ```shell
   ./collect.sh
   ```

   Press Enter only after the Wi-Fi access point or Bluetooth pairing is ready.
   Do not run other diagnostic software concurrently.
8. Wait for the snapshot to finish. The collector continues to the second
   adapter even if the first one fails.
9. Do not clear DTCs, change coding/adaptations, or run actuator tests.
10. Note the context: ignition on or engine idling, ambient conditions, adapter
    labels, and any dashboard warning lamps.

## After the run

1. Save `logs/collect-*.json` and `logs/collect-*.md`.
2. Disconnect the adapter; restore the laptop's normal Wi-Fi network.
3. Inspect the Markdown summary; send both files for analysis.
4. Do not commit the logs. They are ignored by `.gitignore`, but treat them as
   vehicle-related data.

## Failure playbook

| Symptom | First check | Do not |
|---|---|---|
| TCP connection refused/timeout | Adapter AP joined; gateway/IP; correct port | Scan random IPs or ports |
| No Bluetooth serial port | Paired in OS; `--list-ports`; classic SPP vs BLE-only | Assume the serial backend is broken |
| All requests `unsupported` / `NO DATA` | Ignition on; protocol negotiated (`ATDPN`); adapter seated | Blindly increase timeouts |
| One request `timeout` | Adapter busy or still searching; retry the run | Run writes or clear DTCs |
| `7F` negative response | Valid ECU response; record NRC | Treat it as a transport failure |
| Adapter `UNAVAILABLE`/`BUFFER FULL` | Power, other apps, adapter quality | Add retries that hide the fault |
| Empty or partial log | Connection/power/port | Delete the log before analysis |

## What to send back

- `logs/collect-*.json` and `logs/collect-*.md`;
- exact error text if a step failed;
- adapter labels and transport used;
- ignition/engine state and any dashboard warnings.

No VIN or registration plate is requested by the current snapshot. If future
identifiers are added, review [`DATA_AND_SAFETY.md`](DATA_AND_SAFETY.md) before
sharing logs.
