import uuid
from typing import Dict, List, Tuple

from gateway.config import PatientConfig
from gateway.models import DeviceReading


def _full_url() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _resource_reference(full_url: str) -> Dict[str, str]:
    return {"reference": full_url}


class FhirBundleBuilder:
    def __init__(self, patient: PatientConfig) -> None:
        self.patient = patient

    def build(self, readings: List[DeviceReading]) -> Dict[str, object]:
        bundle_entries = []
        patient_full_url, patient_resource = self._build_patient()
        bundle_entries.append({"fullUrl": patient_full_url, "resource": patient_resource})

        for reading in readings:
            device_full_url, device_resource = self._build_device(reading)
            bundle_entries.append({"fullUrl": device_full_url, "resource": device_resource})

            for measurement in reading.measurements:
                observation_full_url = _full_url()
                bundle_entries.append(
                    {
                        "fullUrl": observation_full_url,
                        "resource": {
                            "resourceType": "Observation",
                            "status": "final",
                            "category": [
                                {
                                    "coding": [
                                        {
                                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                            "code": "vital-signs",
                                            "display": "Vital Signs",
                                        }
                                    ]
                                }
                            ],
                            "code": {
                                "coding": [
                                    {
                                        "system": measurement.code_system,
                                        "code": measurement.code,
                                        "display": measurement.display,
                                    }
                                ],
                                "text": measurement.display,
                            },
                            "subject": _resource_reference(patient_full_url),
                            "device": _resource_reference(device_full_url),
                            "effectiveDateTime": measurement.effective_time,
                            "valueQuantity": {
                                "value": measurement.value,
                                "unit": measurement.unit,
                                "system": measurement.system,
                                "code": measurement.unit_code,
                            },
                        },
                    }
                )

        return {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": readings[0].measurements[0].effective_time if readings else None,
            "entry": bundle_entries,
        }

    def _build_patient(self) -> Tuple[str, Dict[str, object]]:
        full_url = _full_url()
        resource: Dict[str, object] = {
            "resourceType": "Patient",
            "identifier": [
                {
                    "system": self.patient.identifier_system,
                    "value": self.patient.identifier_value,
                }
            ],
            "name": [
                {
                    "family": self.patient.family_name,
                    "given": [self.patient.given_name],
                }
            ],
        }
        if self.patient.gender:
            resource["gender"] = self.patient.gender
        if self.patient.birth_date:
            resource["birthDate"] = self.patient.birth_date
        return full_url, resource

    def _build_device(self, reading: DeviceReading) -> Tuple[str, Dict[str, object]]:
        full_url = _full_url()
        resource: Dict[str, object] = {
            "resourceType": "Device",
            "identifier": [
                {
                    "system": "urn:ietf:rfc:3986",
                    "value": f"urn:mac:{reading.address}",
                }
            ],
            "status": "active",
            "deviceName": [{"name": reading.name, "type": "user-friendly-name"}],
        }
        if reading.manufacturer:
            resource["manufacturer"] = reading.manufacturer
        if reading.model:
            resource["modelNumber"] = reading.model
        if reading.serial_number:
            resource["serialNumber"] = reading.serial_number
        return full_url, resource
