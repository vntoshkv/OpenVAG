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

    def test_simulator_snapshot_is_explicitly_read_only_data(self):
        results = collect_read_only_snapshot(self.make_connected_adapter())
        self.assertEqual(results[1]["value"], 1726.0)
        self.assertEqual(results[2]["unit"], "km/h")
        self.assertEqual(results[3]["codes"], [])

    def test_snapshot_retains_unsupported_request_without_losing_other_results(self):
        replies = self.default_replies()
        replies["010D"] = "NO DATA"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(results[2]["status"], "unsupported")
        self.assertEqual(results[3]["status"], "ok")

    def test_multiple_ecu_measurements_are_recorded_separately(self):
        replies = self.default_replies()
        replies["010C"] = ["41 0C 1A F8", "41 0C 0F A0"]
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        measurements = [result for result in results if result["kind"] == "measurement"]
        self.assertEqual([result["value"] for result in measurements], [1726.0, 1000.0, 40.0])
        self.assertEqual([result["response_index"] for result in measurements], [0, 1, 0])

    def test_negative_response_has_its_own_status(self):
        replies = self.default_replies()
        replies["010C"] = "7F 01 12"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(results[1]["status"], "negative")
        self.assertEqual(results[3]["status"], "ok")

    def test_malformed_response_has_its_own_status(self):
        replies = self.default_replies()
        replies["010D"] = "41 0D GG"
        results = collect_read_only_snapshot(self.make_connected_adapter(replies))
        self.assertEqual(results[2]["status"], "malformed")
