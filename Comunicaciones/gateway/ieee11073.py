import math
import struct
from typing import List

from gateway.models import Measurement


def decode_11073_float(raw: bytes) -> float:
    if len(raw) != 4:
        raise ValueError("IEEE 11073 FLOAT requires 4 bytes")

    raw_mantissa = raw[0] | (raw[1] << 8) | (raw[2] << 16)
    exponent = struct.unpack("b", bytes([raw[3]]))[0]

    special = {
        0x007FFFFE: math.inf,
        0x007FFFFF: math.nan,
        0x00800000: math.nan,
        0x00800001: math.nan,
        0x00800002: -math.inf,
    }
    if raw_mantissa in special:
        return special[raw_mantissa]

    mantissa = raw_mantissa
    if mantissa >= 0x800000:
        mantissa = -((0x1000000 - mantissa) & 0xFFFFFF)

    return mantissa * pow(10, exponent)


def decode_11073_sfloat(raw: bytes) -> float:
    if len(raw) != 2:
        raise ValueError("IEEE 11073 SFLOAT requires 2 bytes")

    value = int.from_bytes(raw, byteorder="little", signed=False)
    raw_mantissa = value & 0x0FFF
    mantissa = raw_mantissa
    exponent = (value >> 12) & 0x000F

    special = {
        0x07FE: math.inf,
        0x07FF: math.nan,
        0x0800: math.nan,
        0x0801: math.nan,
        0x0802: -math.inf,
    }
    if raw_mantissa in special:
        return special[raw_mantissa]

    if mantissa >= 0x0800:
        mantissa = -((0x1000 - mantissa) & 0x0FFF)
    if exponent >= 0x0008:
        exponent = -((0x0010 - exponent) & 0x000F)

    return mantissa * pow(10, exponent)


def parse_temperature_measurement(raw: bytes) -> List[Measurement]:
    if len(raw) < 5:
        raise ValueError("Temperature measurement payload is incomplete")

    flags = raw[0]
    unit = "Cel" if (flags & 0x01) == 0 else "[degF]"
    display_unit = "°C" if unit == "Cel" else "°F"
    value = round(decode_11073_float(raw[1:5]), 2)
    return [
        Measurement(
            code="8310-5",
            display="Body temperature",
            value=value,
            unit=display_unit,
            system="http://unitsofmeasure.org",
            unit_code=unit,
        )
    ]


def parse_blood_pressure_measurement(raw: bytes) -> List[Measurement]:
    if len(raw) < 7:
        raise ValueError("Blood pressure measurement payload is incomplete")

    flags = raw[0]
    unit_code = "mm[Hg]" if (flags & 0x01) == 0 else "kPa"
    display_unit = "mmHg" if unit_code == "mm[Hg]" else "kPa"

    measurements = [
        Measurement("8480-6", "Systolic blood pressure", round(decode_11073_sfloat(raw[1:3]), 2), display_unit, "http://unitsofmeasure.org", unit_code),
        Measurement("8462-4", "Diastolic blood pressure", round(decode_11073_sfloat(raw[3:5]), 2), display_unit, "http://unitsofmeasure.org", unit_code),
        Measurement("8478-0", "Mean blood pressure", round(decode_11073_sfloat(raw[5:7]), 2), display_unit, "http://unitsofmeasure.org", unit_code),
    ]

    offset = 7
    if flags & 0x02:
        offset += 7
    if flags & 0x04:
        if len(raw) < offset + 2:
            raise ValueError("Blood pressure payload is missing pulse rate bytes")
        measurements.append(
            Measurement(
                code="8867-4",
                display="Heart rate",
                value=round(decode_11073_sfloat(raw[offset:offset + 2]), 2),
                unit="beats/minute",
                system="http://unitsofmeasure.org",
                unit_code="/min",
            )
        )

    return measurements


def parse_weight_measurement(raw: bytes) -> List[Measurement]:
    if len(raw) < 3:
        raise ValueError("Weight measurement payload is incomplete")

    flags = raw[0]
    unit_code = "kg" if (flags & 0x01) == 0 else "[lb_av]"
    display_unit = "kg" if unit_code == "kg" else "lb"
    resolution = 0.005 if unit_code == "kg" else 0.01
    weight = round(int.from_bytes(raw[1:3], byteorder="little", signed=False) * resolution, 2)

    return [
        Measurement(
            code="29463-7",
            display="Body weight",
            value=weight,
            unit=display_unit,
            system="http://unitsofmeasure.org",
            unit_code=unit_code,
        )
    ]
