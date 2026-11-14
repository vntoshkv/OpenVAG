import unittest

from openvag.errors import MalformedResponseError
from openvag.obd import decode_dtc_response, decode_engine_rpm, decode_supported_pids, decode_vehicle_speed


class ObdDecoderTests(unittest.TestCase):
    def test_decodes_standard_measurements(self):
        self.assertEqual(decode_engine_rpm([0x41, 0x0C, 0x1A, 0xF8]).value, 1726.0)
        self.assertEqual(decode_vehicle_speed([0x41, 0x0D, 0x28]).value, 40.0)

    def test_decodes_dtc_and_ignores_padding(self):
        self.assertEqual(decode_dtc_response([0x43, 0x01, 0x33, 0x00, 0x00]), ["P0133"])

    def test_decodes_pid_availability_bitmap(self):
        self.assertEqual(decode_supported_pids([0x41, 0x00, 0x80, 0x00, 0x00, 0x01]), [1, 32])

    def test_rejects_wrong_response_prefix(self):
        with self.assertRaises(MalformedResponseError):
            decode_engine_rpm([0x41, 0x0D, 0x00])
