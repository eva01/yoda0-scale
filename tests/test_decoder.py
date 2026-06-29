import unittest

from yoda0_scale.decoder import decode_manufacturer_data, decode_records


class DecoderTests(unittest.TestCase):
    def test_decode_loaded_payload_uses_big_endian_centi_kg(self) -> None:
        reading = decode_manufacturer_data("C0091D4C1388000025000000000000")

        self.assertIsNotNone(reading)
        assert reading is not None
        self.assertEqual(reading.weight_kg, 75.0)
        self.assertIs(reading.loaded, True)
        self.assertEqual(reading.sequence, 9)
        self.assertEqual(reading.raw_weight, 7500)

    def test_decode_fractional_payload(self) -> None:
        reading = decode_manufacturer_data("C00A1D811388000025000000000000")

        self.assertIsNotNone(reading)
        assert reading is not None
        self.assertEqual(reading.weight_kg, 75.53)
        self.assertIs(reading.loaded, True)
        self.assertEqual(reading.sequence, 10)
        self.assertEqual(reading.raw_weight, 7553)

    def test_decode_idle_payload_as_unloaded_zero(self) -> None:
        reading = decode_manufacturer_data("C00700000000000024000000000000")

        self.assertIsNotNone(reading)
        assert reading is not None
        self.assertEqual(reading.weight_kg, 0)
        self.assertIs(reading.loaded, False)
        self.assertEqual(reading.sequence, 7)

    def test_decode_rejects_non_yoda0_payloads(self) -> None:
        self.assertIsNone(decode_manufacturer_data("4C0012020002"))
        self.assertIsNone(decode_manufacturer_data(""))

    def test_decode_records_returns_loaded_readings_only_when_requested(self) -> None:
        records = [
            {
                "timestamp": "2026-06-29T13:00:00Z",
                "name": "Yoda0",
                "id": "device",
                "rssi": -52,
                "manufacturerData": "C00700000000000024000000000000",
            },
            {
                "timestamp": "2026-06-29T13:00:01Z",
                "name": "Yoda0",
                "id": "device",
                "rssi": -51,
                "manufacturerData": "C0091D4C1388000025000000000000",
            },
        ]

        readings = list(decode_records(records, loaded_only=True))

        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0].weight_kg, 75.0)
        self.assertEqual(readings[0].rssi, -51)


if __name__ == "__main__":
    unittest.main()
