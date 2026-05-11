from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Measurement:
    code: str
    display: str
    value: float
    unit: str
    system: str
    unit_code: str
    code_system: str = "http://loinc.org"
    effective_time: str = field(default_factory=utc_now)


@dataclass
class DeviceReading:
    address: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    measurements: List[Measurement] = field(default_factory=list)
