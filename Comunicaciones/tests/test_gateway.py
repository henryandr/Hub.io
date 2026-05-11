import unittest

from gateway.config import PatientConfig
from gateway.fhir import FhirBundleBuilder
from gateway.ieee11073 import (
    decode_11073_float,
    decode_11073_sfloat,
    parse_blood_pressure_measurement,
    parse_temperature_measurement,
    parse_weight_measurement,
)
from gateway.models import DeviceReading


class Ieee11073Tests(unittest.TestCase):
    def test_decode_float(self) -> None:
        self.assertEqual(decode_11073_float(bytes([0xED, 0x0E, 0x00, 0xFE])), 38.21)

    def test_decode_sfloat(self) -> None:
        self.assertEqual(decode_11073_sfloat(bytes([0x76, 0x00])), 118)

    def test_parse_blood_pressure(self) -> None:
        measurements = parse_blood_pressure_measurement(bytes([0x04, 0x76, 0x00, 0x4C, 0x00, 0x5E, 0x00, 0x48, 0x00]))
        self.assertEqual([measurement.code for measurement in measurements], ["8480-6", "8462-4", "8478-0", "8867-4"])

    def test_parse_temperature(self) -> None:
        measurement = parse_temperature_measurement(bytes([0x00, 0xED, 0x0E, 0x00, 0xFE]))[0]
        self.assertEqual(measurement.code, "8310-5")
        self.assertEqual(measurement.unit_code, "Cel")

    def test_parse_weight(self) -> None:
        measurement = parse_weight_measurement(bytes([0x00, 0x20, 0x4E]))[0]
        self.assertEqual(measurement.value, 100.0)


class FhirBundleTests(unittest.TestCase):
    def test_build_bundle(self) -> None:
        reading = DeviceReading(
            address="00:11:22:33:44:55",
            name="Thermometer",
            manufacturer="Hub.io",
            model="TMP-1",
            serial_number="ABC123",
            measurements=parse_temperature_measurement(bytes([0x00, 0xED, 0x0E, 0x00, 0xFE])),
        )
        bundle = FhirBundleBuilder(
            PatientConfig(
                identifier_system="https://hub.io/patients",
                identifier_value="patient-1",
                given_name="Ada",
                family_name="Lovelace",
            )
        ).build([reading])

        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "collection")
        self.assertEqual(len(bundle["entry"]), 3)
        self.assertEqual(bundle["entry"][0]["resource"]["resourceType"], "Patient")
        self.assertEqual(bundle["entry"][1]["resource"]["resourceType"], "Device")
        self.assertEqual(bundle["entry"][2]["resource"]["resourceType"], "Observation")


if __name__ == "__main__":
    unittest.main()
