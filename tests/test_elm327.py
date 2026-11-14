import unittest

from openvag.elm327 import Elm327Adapter
from openvag.errors import ConnectionFailedError, ServiceUnsupportedError, TransportTimeoutError
from openvag.simulator import SimulatedElm327Transport


class Elm327AdapterTests(unittest.TestCase):
    def test_connect_reports_simulated_adapter_capabilities(self):
        adapter = Elm327Adapter(SimulatedElm327Transport())
        capabilities = adapter.connect()
        self.assertEqual(capabilities.version, "ELM327 VSIM 1.0")
        self.assertEqual(capabilities.initialization["ATSP0"], "OK")

    def test_rejects_non_allowlisted_request(self):
        adapter = Elm327Adapter(SimulatedElm327Transport())
        adapter.connect()
        with self.assertRaises(ValueError):
            adapter.request_obd("04")

    def test_normalizes_no_data_as_unsupported(self):
        replies = {"ATZ": "ELM", "ATE0": "OK", "ATL0": "OK", "ATS0": "OK", "ATH0": "OK", "ATSP0": "OK", "010C": "NO DATA"}
        adapter = Elm327Adapter(SimulatedElm327Transport(replies))
        adapter.connect()
        with self.assertRaises(ServiceUnsupportedError):
            adapter.request_obd("010C")

    def test_failed_initialization_is_connection_error(self):
        adapter = Elm327Adapter(SimulatedElm327Transport({"ATZ": "ERROR"}))
        with self.assertRaises(ConnectionFailedError):
            adapter.connect()


class TimeoutTransport(SimulatedElm327Transport):
    def request(self, command, timeout_seconds):
        raise TimeoutError


class TimeoutTests(unittest.TestCase):
    def test_normalizes_timeouts(self):
        with self.assertRaises(TransportTimeoutError):
            Elm327Adapter(TimeoutTransport()).connect()
