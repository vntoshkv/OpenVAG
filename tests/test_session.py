import json
import tempfile
import unittest
from pathlib import Path

from openvag.cli import collect_read_only_snapshot
from openvag.elm327 import Elm327Adapter
from openvag.session import DiagnosticSession
from openvag.simulator import SimulatedElm327Transport


class SessionTests(unittest.TestCase):
    def test_save_writes_timestamped_simulator_session(self):
        session = DiagnosticSession.create("simulator", "ELM327 vSIM", [])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "session.json"
            session.save(target)
            saved = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(saved["source"], "simulator")
        self.assertIn("+00:00", saved["created_at"])

    def test_simulator_snapshot_is_explicitly_read_only_data(self):
        adapter = Elm327Adapter(SimulatedElm327Transport())
        adapter.connect()
        results = collect_read_only_snapshot(adapter)
        self.assertEqual(results[1]["value"], 1726.0)
        self.assertEqual(results[2]["unit"], "km/h")
        self.assertEqual(results[3]["codes"], [])

    def test_snapshot_retains_unsupported_request_without_losing_other_results(self):
        replies = SimulatedElm327Transport().replies.copy()
        replies["010D"] = "NO DATA"
        adapter = Elm327Adapter(SimulatedElm327Transport(replies))
        adapter.connect()
        results = collect_read_only_snapshot(adapter)
        self.assertEqual(results[2]["status"], "unsupported")
        self.assertEqual(results[3]["status"], "ok")
