import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from openvag.cli import main
from openvag.simulator import SimulatedElm327Transport


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
            self.assertEqual(payload["adapter"]["transport"], "simulator")

            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved["source"], "simulator")
            self.assertEqual(saved["adapter"]["protocol"], "A6")
            self.assertEqual(len(saved["results"]), 4)

    def test_serial_option_wires_the_serial_transport_and_baud(self):
        with patch("openvag.cli.SerialLineTransport") as transport_class:
            transport_class.return_value = SimulatedElm327Transport()
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--serial", "/dev/cu.ELM327-TEST", "--baud", "9600"])

            self.assertEqual(code, 0)
            transport_class.assert_called_once_with("/dev/cu.ELM327-TEST", baudrate=9600)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["source"], "real")
            self.assertEqual(payload["adapter"]["transport"], "serial")
