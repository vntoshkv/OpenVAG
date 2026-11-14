import unittest

from openvag.elm327 import Elm327Adapter
from openvag.errors import AdapterUnavailableError, TransportTimeoutError
from openvag.serial_transport import SerialLineTransport


class FakeSerial:
    def __init__(self, replies, initial=b""):
        self.replies = replies
        self.commands = []
        self.buffer = bytearray(initial)
        self.closed = False
        self.timeout = 0.1

    def write(self, data):
        command = data.decode("ascii").strip()
        self.commands.append(command)
        reply = self.replies.get(command, "NO DATA")
        body = "\r".join(reply) if isinstance(reply, (list, tuple)) else reply
        self.buffer.extend((body + "\r\r>").encode("ascii"))

    def read(self, size):
        chunk = bytes(self.buffer[:size])
        del self.buffer[:size]
        return chunk

    def flush(self):
        pass

    def reset_input_buffer(self):
        self.buffer.clear()

    def close(self):
        self.closed = True


class SilentSerial(FakeSerial):
    def write(self, data):
        self.commands.append(data.decode("ascii").strip())


class SerialTransportTests(unittest.TestCase):
    def make_transport(self, serial_device):
        return SerialLineTransport(
            "/dev/fake",
            serial_factory=lambda port, baudrate: serial_device,
        )

    def test_request_returns_lines_without_prompt(self):
        device = FakeSerial({"ATZ": "ELM327 v1.5"})
        transport = self.make_transport(device)
        self.addCleanup(transport.close)

        self.assertEqual(transport.request("ATZ", 1.0), ["ELM327 v1.5"])
        self.assertEqual(device.commands, ["ATZ"])

    def test_adapter_connects_and_reads_values_over_serial(self):
        replies = {
            "ATZ": "ELM327 v1.5",
            "ATE0": "OK",
            "ATL0": "OK",
            "ATS0": "OK",
            "ATH0": "OK",
            "ATSP0": "OK",
            "ATI": "ELM327 v1.5",
            "AT@1": "OBDII to RS232 Interpreter",
            "ATDPN": "A6",
            "010C": ["41 0C 1A F8", "41 0C 0F A0"],
            "03": "43 00 00",
        }
        device = FakeSerial(replies)
        adapter = Elm327Adapter(self.make_transport(device))
        self.addCleanup(adapter.close)

        capabilities = adapter.connect()
        self.assertEqual(capabilities.version, "ELM327 V1.5")
        self.assertEqual(capabilities.protocol, "A6")
        responses = adapter.request_obd("010C")
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[1].values, (0x41, 0x0C, 0x0F, 0xA0))
        self.assertEqual(adapter.describe_protocol(), "A6")

        adapter.close()
        self.assertTrue(device.closed)

    def test_timeout_is_normalized_and_closes_device(self):
        device = SilentSerial({})
        transport = self.make_transport(device)
        self.addCleanup(transport.close)

        with self.assertRaises(TransportTimeoutError):
            transport.request("ATZ", 0.2)
        self.assertTrue(device.closed)

    def test_write_error_is_adapter_unavailable(self):
        class BrokenSerial(FakeSerial):
            def write(self, data):
                raise OSError("broken pipe")

        transport = self.make_transport(BrokenSerial({}))
        self.addCleanup(transport.close)
        with self.assertRaises(AdapterUnavailableError):
            transport.request("ATZ", 0.2)
