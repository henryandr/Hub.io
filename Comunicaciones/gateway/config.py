import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PatientConfig:
    identifier_system: str = "urn:ietf:rfc:3986"
    identifier_value: str = "urn:uuid:hub-io-patient"
    given_name: str = "Hub"
    family_name: str = "Patient"
    gender: Optional[str] = None
    birth_date: Optional[str] = None


@dataclass
class BackendConfig:
    endpoint_url: str = "http://localhost:8080/fhir"
    auth_token: Optional[str] = None
    timeout_seconds: int = 10
    verify_tls: bool = True


@dataclass
class BleConfig:
    scan_duration_seconds: int = 8
    notification_timeout_seconds: int = 5
    device_name_prefixes: List[str] = field(default_factory=list)
    device_address_allowlist: List[str] = field(default_factory=list)
    mock_mode: bool = False


@dataclass
class GatewayConfig:
    log_level: str = "INFO"
    poll_interval_seconds: int = 30
    run_once: bool = False
    patient: PatientConfig = field(default_factory=PatientConfig)
    backend: BackendConfig = field(default_factory=BackendConfig)
    ble: BleConfig = field(default_factory=BleConfig)


def load_config(path: str) -> GatewayConfig:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return GatewayConfig(
        log_level=raw.get("log_level", "INFO"),
        poll_interval_seconds=raw.get("poll_interval_seconds", 30),
        run_once=raw.get("run_once", False),
        patient=PatientConfig(**raw.get("patient", {})),
        backend=BackendConfig(**raw.get("backend", {})),
        ble=BleConfig(**raw.get("ble", {})),
    )
