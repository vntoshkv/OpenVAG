import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from openvag.cli import main


class CliTests(unittest.TestCase):
    def test_simulate_end_to_end_and_session_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "session.json"
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--simulate", "--session", str(target)])

            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["source"], "simulator")
            self.assertEqual(payload["adapter"]["protocol"], "A6")

            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved["source"], "simulator")
            self.assertEqual(saved["adapter"]["protocol"], "A6")
            self.assertEqual(len(saved["results"]), 4)
