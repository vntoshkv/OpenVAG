import unittest

from openvag.elm327 import Elm327Adapter
from openvag.errors import (
    AdapterUnavailableError,
    ConnectionFailedError,
    MalformedResponseError,
    ProtocolNegativeResponseError,
    ServiceUnsupportedError,
    TransportTimeoutError,
)
from openvag.simulator import SimulatedElm327Transport


class Elm327AdapterTests(unittest.TestCase):
    def make_adapter(self, replies=None):
        adapter = Elm327Adapter(SimulatedElm327Transport(replies))
        self.addCleanup(adapter.close)
        return adapter

    def default_replies(self):
        return SimulatedElm327Transport().replies.copy()

    def test_connect_reports_simulated_capabilities(self):
        capabilities = self.make_adapter().connect()
        self.assertEqual(capabilities.version, "ELM327 VSIM 1.0")
        self.assertEqual(capabilities.description, "OBDII TO RS232 INTERPRETER")
        self.assertEqual(capabilities.protocol, "A6")
        self.assertEqual(capabilities.initialization["ATSP0"], "OK")

    def test_rejects_non_allowlisted_request(self):
        adapter = self.make_adapter()
        adapter.connect()
        with self.assertRaises(ValueError):
            adapter.request_obd("04")

    def test_normalizes_no_data_as_unsupported(self):
        replies = self.default_replies()
        replies["010C"] = "NO DATA"
        adapter = self.make_adapter(replies)
        adapter.connect()
        with self.assertRaises(ServiceUnsupportedError):
            adapter.request_obd("010C")

    def test_failed_initialization_is_connection_error(self):
        adapter = self.make_adapter({"ATZ": "ERROR"})
        with self.assertRaises(ConnectionFailedError):
            adapter.connect()

    def test_request_before_connect_is_connection_error(self):
        with self.assertRaises(ConnectionFailedError):
            self.make_adapter().request_obd("0100")

    def test_echo_and_searching_prefix_are_ignored(self):
        replies = self.default_replies()
        replies["ATZ"] = "ATZ\r\rELM327 v1.5"
        replies["ATI"] = "ATI\r\rELM327 v1.5"
        replies["010C"] = "SEARCHING...\r41 0C 1A F8"
        adapter = self.make_adapter(replies)
        capabilities = adapter.connect()
        self.assertEqual(capabilities.version, "ELM327 V1.5")
        self.assertEqual(adapter.request_obd("010C")[0].values, (0x41, 0x0C, 0x1A, 0xF8))

    def test_bus_init_prefix_on_same_line(self):
        replies = self.default_replies()
        replies["010D"] = "BUS INIT: OK 41 0D 28"
        adapter = self.make_adapter(replies)
        adapter.connect()
        self.assertEqual(adapter.request_obd("010D")[0].values, (0x41, 0x0D, 0x28))

    def test_multiple_ecu_responses_are_preserved(self):
        replies = self.default_replies()
        replies["010C"] = ["41 0C 1A F8", "41 0C 0F A0"]
        adapter = self.make_adapter(replies)
        adapter.connect()
        responses = adapter.request_obd("010C")
        self.assertEqual([response.response_index for response in responses], [0, 1])
        self.assertEqual([response.values for response in responses], [(0x41, 0x0C, 0x1A, 0xF8), (0x41, 0x0C, 0x0F, 0xA0)])

    def test_negative_response_keeps_nrc(self):
        replies = self.default_replies()
        replies["010C"] = "7F 01 12"
        adapter = self.make_adapter(replies)
        adapter.connect()
        with self.assertRaises(ProtocolNegativeResponseError) as caught:
            adapter.request_obd("010C")
        self.assertEqual(caught.exception.nrc, 0x12)

    def test_adapter_error_is_normalized(self):
        replies = self.default_replies()
        replies["010C"] = "BUFFER FULL"
        adapter = self.make_adapter(replies)
        adapter.connect()
        with self.assertRaises(AdapterUnavailableError):
            adapter.request_obd("010C")

    def test_malformed_data_is_rejected(self):
        replies = self.default_replies()
        replies["010C"] = "41 0C GG"
        adapter = self.make_adapter(replies)
        adapter.connect()
        with self.assertRaises(MalformedResponseError):
            adapter.request_obd("010C")

    def test_optional_identification_failure_falls_back_to_atz_version(self):
        replies = self.default_replies()
        replies["ATI"] = "?"
        replies["AT@1"] = "?"
        replies["ATDPN"] = "?"
        adapter = self.make_adapter(replies)
        capabilities = adapter.connect()
        self.assertEqual(capabilities.version, "ELM327 VSIM 1.0")
        self.assertEqual(capabilities.description, "unknown")
        self.assertEqual(capabilities.protocol, "unknown")

    def test_describe_protocol_refreshes_negotiated_value(self):
        replies = self.default_replies()
        adapter = self.make_adapter(replies)
        adapter.connect()
        replies["ATDPN"] = "A6"
        self.assertEqual(adapter.describe_protocol(), "A6")


class TimeoutTransport(SimulatedElm327Transport):
    def request(self, command, timeout_seconds):
        raise TimeoutError


class TimeoutTests(unittest.TestCase):
    def test_normalizes_timeouts(self):
        adapter = Elm327Adapter(TimeoutTransport())
        self.addCleanup(adapter.close)
        with self.assertRaises(TransportTimeoutError):
            adapter.connect()
