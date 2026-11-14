import json
import tempfile
import unittest
from pathlib import Path

from openvag.cli import collect_read_only_snapshot
from openvag.elm327 import Elm327Adapter
from openvag.session import DiagnosticSession
from openvag.simulator import SimulatedElm327Transport


class SessionTests(unittest.TestCase):
    def make_connected_adapter(self, replies=None):
        adapter = Elm327Adapter(SimulatedElm327Transport(replies))
        self.addCleanup(adapter.close)
        adapter.connect()
        return adapter

    def default_replies(self):
        return SimulatedElm327Transport().replies.copy()

    @staticmethod
    def by_request(results, request):
        return [result for result in results if result.get("request") == request]

    def test_save_writes_timestamped_simulator_session(self):
        session = DiagnosticSession.create(
            "simulator",
            "ELM327 vSIM",
            [],
            adapter={"version": "ELM327 vSIM", "protocol": "A6"},
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "session.json"
            session.save(target)
            saved = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(saved["source"], "simulator")
        self.assertIn("+00:00", saved["created_at"])
        self.assertEqual(saved["adapter"]["protocol"], "A6")

    def test_simulator_snapshot_contains_core_read_only_data(self):
        results = collect_read_only_snapshot(self.make_connected_adapter())
        by_request = {result["request"]: result for result in results if result["status"] == "ok"}
        self.assertEqual(by_request["010C"]["value"], 1726.0)
        self.assertEqual(by_request["010D"]["unit"], "km/h")
        self.assertEqual(by_request["03"]["codes"], [])
        self.assertEqual(by_request["07"]["codes"], [])
        self.assertEqual(by_request["0A"]["codes"], [])
        self.assertIn("0120", by_request)
        self.assertIn("0140", by_request)

    def test_snapshot_retains_unsupported_request_without_losing_other_results(self):
        replies = self.default_replies()
        replies["010D"] = "NO DATA"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(self.by_request(results, "010D")[0]["status"], "unsupported")
        self.assertEqual(self.by_request(results, "03")[0]["status"], "ok")

    def test_multiple_ecu_measurements_are_recorded_separately(self):
        replies = self.default_replies()
        replies["010C"] = ["41 0C 1A F8", "41 0C 0F A0"]
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        entries = self.by_request(results, "010C")
        self.assertEqual([entry["value"] for entry in entries], [1726.0, 1000.0])
        self.assertEqual([entry["response_index"] for entry in entries], [0, 1])

    def test_negative_response_has_its_own_status(self):
        replies = self.default_replies()
        replies["010C"] = "7F 01 12"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(self.by_request(results, "010C")[0]["status"], "negative")
        self.assertEqual(self.by_request(results, "03")[0]["status"], "ok")

    def test_malformed_response_has_its_own_status(self):
        replies = self.default_replies()
        replies["010D"] = "41 0D GG"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(self.by_request(results, "010D")[0]["status"], "malformed")

    def test_unadvertised_pids_are_not_requested(self):
        replies = self.default_replies()
        replies["0100"] = "41 00 00 00 00 00"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        requests = {result["request"] for result in results}
        self.assertNotIn("0104", requests)
        self.assertNotIn("0120", requests)
        self.assertNotIn("0140", requests)
        self.assertIn("010C", requests)
        self.assertIn("010D", requests)

    def test_0101_monitor_status_is_decoded(self):
        results = collect_read_only_snapshot(self.make_connected_adapter())
        entry = self.by_request(results, "0101")[0]
        self.assertFalse(entry["mil_on"])
        self.assertEqual(entry["dtc_count"], 0)
        self.assertEqual(entry["readiness_bytes"], (7, 101, 0))
