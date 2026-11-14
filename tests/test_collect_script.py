import argparse
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_logs.py"
_SPEC = importlib.util.spec_from_file_location("openvag_collect_logs", _SCRIPT_PATH)
collect_logs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(collect_logs)


class CollectLogsScriptTests(unittest.TestCase):
    def test_parse_endpoint(self):
        self.assertEqual(collect_logs.parse_endpoint("192.168.0.10:35000"), ("192.168.0.10", 35000))
        with self.assertRaises(argparse.ArgumentTypeError):
            collect_logs.parse_endpoint("missing-port")

    def test_status_and_pid_summary_helpers(self):
        results = [
            {"status": "ok", "kind": "capabilities", "supported_pids": [1, 12]},
            {"status": "ok", "kind": "measurement", "request": "010C"},
            {"status": "unsupported", "kind": "measurement", "request": "0110"},
            {"status": "ok", "kind": "capabilities", "supported_pids": [13, 12]},
        ]
        self.assertEqual(collect_logs.count_statuses(results), {"ok": 3, "unsupported": 1})
        self.assertEqual(collect_logs.supported_pids(results), [1, 12, 13])

    def test_render_markdown_contains_run_and_measurement(self):
        combined = {
            "created_at": "2026-11-14T00:00:00+00:00",
            "environment": {"system": "TestOS", "machine": "test64", "python": "3.9.0"},
            "runs": [
                {
                    "transport": "tcp",
                    "endpoint": "127.0.0.1:35000",
                    "status": "ok",
                    "error": None,
                    "adapter": {
                        "version": "ELM327 vTEST",
                        "description": "TEST",
                        "protocol": "A6",
                        "transport": "tcp",
                        "voltage": "12.6V",
                    },
                    "duration_s": 0.1,
                    "counts": {"ok": 1},
                    "supported_pids": [0x0C],
                    "dtcs": {"dtcs": [], "pending_dtcs": [], "permanent_dtcs": []},
                    "results": [
                        {
                            "status": "ok",
                            "kind": "measurement",
                            "request": "010C",
                            "name": "engine_rpm",
                            "value": 1726.0,
                            "unit": "rpm",
                            "raw_hex": "41 0C 1A F8",
                        }
                    ],
                }
            ],
        }
        report = collect_logs.render_markdown(combined)
        self.assertIn("OpenVAG read-only collection", report)
        self.assertIn("engine_rpm", report)
        self.assertIn("1726.000", report)
        self.assertIn("127.0.0.1:35000", report)

    def test_simulate_writes_dry_run_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = collect_logs.main(["--simulate", "--output-dir", directory])
            self.assertEqual(code, 0)

            json_files = sorted(Path(directory).glob("collect-*.json"))
            markdown_files = sorted(Path(directory).glob("collect-*.md"))
            self.assertEqual(len(json_files), 1)
            self.assertEqual(len(markdown_files), 1)

            data = json.loads(json_files[0].read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "openvag-collect-1")
            self.assertEqual(len(data["runs"]), 1)
            run = data["runs"][0]
            self.assertEqual(run["transport"], "simulator")
            self.assertEqual(run["status"], "ok")
            self.assertGreaterEqual(len(run["results"]), 20)
            self.assertEqual(run["adapter"]["transport"], "simulator")
