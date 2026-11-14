import unittest

from openvag.errors import MalformedResponseError
from openvag.obd import (
    PID_DECODERS,
    decode_dtc_response,
    decode_engine_rpm,
    decode_monitor_status,
    decode_pending_dtc_response,
    decode_permanent_dtc_response,
    decode_supported_pids,
    decode_vehicle_speed,
)


class ObdDecoderTests(unittest.TestCase):
    def test_decodes_standard_measurements(self):
        self.assertEqual(decode_engine_rpm([0x41, 0x0C, 0x1A, 0xF8]).value, 1726.0)
        self.assertEqual(decode_vehicle_speed([0x41, 0x0D, 0x28]).value, 40.0)

    def test_decodes_dtc_and_ignores_padding(self):
        self.assertEqual(decode_dtc_response([0x43, 0x01, 0x33, 0x00, 0x00]), ["P0133"])

    def test_decodes_pending_and_permanent_dtcs(self):
        self.assertEqual(decode_pending_dtc_response([0x47, 0x01, 0x33, 0x00, 0x00]), ["P0133"])
        self.assertEqual(decode_permanent_dtc_response([0x4A, 0x01, 0x71]), ["P0171"])

    def test_decodes_pid_availability_bitmap(self):
        self.assertEqual(decode_supported_pids([0x41, 0x00, 0x80, 0x00, 0x00, 0x01]), [1, 32])

    def test_decodes_extended_pid_availability_bitmaps(self):
        self.assertEqual(decode_supported_pids([0x41, 0x20, 0x80, 0x00, 0x00, 0x00], 0x20), [33])
        self.assertEqual(decode_supported_pids([0x41, 0x40, 0x00, 0x00, 0x00, 0x01], 0x40), [96])

    def test_decodes_monitor_status_mil_and_dtc_count(self):
        status = decode_monitor_status([0x41, 0x01, 0x82, 0x07, 0x65, 0x00])
        self.assertTrue(status.mil_on)
        self.assertEqual(status.dtc_count, 2)
        self.assertEqual(status.readiness_bytes, (7, 101, 0))

    def test_decodes_all_live_pid_formulas(self):
        cases = (
            (0x04, [0x41, 0x04, 0x80], 50.19607843137255, "%"),
            (0x05, [0x41, 0x05, 0x5A], 50.0, "°C"),
            (0x06, [0x41, 0x06, 0x80], 0.0, "%"),
            (0x06, [0x41, 0x06, 0x00], -100.0, "%"),
            (0x07, [0x41, 0x07, 0xC0], 50.0, "%"),
            (0x08, [0x41, 0x08, 0x80], 0.0, "%"),
            (0x09, [0x41, 0x09, 0x80], 0.0, "%"),
            (0x0A, [0x41, 0x0A, 0x0A], 30.0, "kPa"),
            (0x0B, [0x41, 0x0B, 0x64], 100.0, "kPa"),
            (0x0C, [0x41, 0x0C, 0x1A, 0xF8], 1726.0, "rpm"),
            (0x0D, [0x41, 0x0D, 0x28], 40.0, "km/h"),
            (0x0E, [0x41, 0x0E, 0x80], 0.0, "°"),
            (0x0F, [0x41, 0x0F, 0x50], 40.0, "°C"),
            (0x10, [0x41, 0x10, 0x0C, 0x80], 32.0, "g/s"),
            (0x11, [0x41, 0x11, 0x40], 25.098039215686274, "%"),
            (0x1F, [0x41, 0x1F, 0x01, 0x2C], 300.0, "s"),
            (0x21, [0x41, 0x21, 0x00, 0x0A], 10.0, "km"),
            (0x2F, [0x41, 0x2F, 0x80], 50.19607843137255, "%"),
            (0x31, [0x41, 0x31, 0x00, 0x64], 100.0, "km"),
            (0x33, [0x41, 0x33, 0x65], 101.0, "kPa"),
            (0x42, [0x41, 0x42, 0x30, 0x39], 12.345, "V"),
            (0x46, [0x41, 0x46, 0x50], 40.0, "°C"),
            (0x5C, [0x41, 0x5C, 0x5A], 50.0, "°C"),
            (0x5E, [0x41, 0x5E, 0x03, 0xE8], 50.0, "L/h"),
        )
        for pid, response, expected, unit in cases:
            with self.subTest(pid=pid):
                measurement = PID_DECODERS[pid](response)
                self.assertAlmostEqual(measurement.value, expected)
                self.assertEqual(measurement.unit, unit)
                self.assertEqual(measurement.request, "01{:02X}".format(pid))

    def test_rejects_wrong_response_prefix(self):
        with self.assertRaises(MalformedResponseError):
            decode_engine_rpm([0x41, 0x0D, 0x00])

    def test_rejects_truncated_extended_response(self):
        with self.assertRaises(MalformedResponseError):
            PID_DECODERS[0x42]([0x41, 0x42, 0x30])
