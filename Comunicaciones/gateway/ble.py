import asyncio
import logging
from typing import Dict, List, Optional

from gateway.config import BleConfig
from gateway.ieee11073 import (
    parse_blood_pressure_measurement,
    parse_temperature_measurement,
    parse_weight_measurement,
)
from gateway.models import DeviceReading, Measurement

LOGGER = logging.getLogger(__name__)

STANDARD_CHARACTERISTICS = {
    "device_name": "00002a00-0000-1000-8000-00805f9b34fb",
    "manufacturer_name": "00002a29-0000-1000-8000-00805f9b34fb",
    "model_number": "00002a24-0000-1000-8000-00805f9b34fb",
    "serial_number": "00002a25-0000-1000-8000-00805f9b34fb",
    "battery_level": "00002a19-0000-1000-8000-00805f9b34fb",
    "temperature_measurement": "00002a1c-0000-1000-8000-00805f9b34fb",
    "blood_pressure_measurement": "00002a35-0000-1000-8000-00805f9b34fb",
    "weight_measurement": "00002a9d-0000-1000-8000-00805f9b34fb",
}


class BleGateway:
    def __init__(self, config: BleConfig) -> None:
        self.config = config

    async def collect(self) -> List[DeviceReading]:
        if self.config.mock_mode:
            return self._mock_readings()

        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as exc:
            raise RuntimeError("Install bleak to enable BLE capture on Raspberry Pi 4") from exc

        discovered = await BleakScanner.discover(timeout=self.config.scan_duration_seconds)
        devices = [device for device in discovered if self._matches_filters(device)]
        readings: List[DeviceReading] = []

        for device in devices:
            reading = await self._read_device(BleakClient, device)
            if reading and reading.measurements:
                readings.append(reading)

        return readings

    def _matches_filters(self, device) -> bool:
        if self.config.device_address_allowlist and device.address not in self.config.device_address_allowlist:
            return False

        if self.config.device_name_prefixes:
            name = device.name or ""
            return any(name.startswith(prefix) for prefix in self.config.device_name_prefixes)

        return True

    async def _read_device(self, bleak_client_cls, device) -> Optional[DeviceReading]:
        LOGGER.info("Connecting to %s (%s)", device.name, device.address)

        async with bleak_client_cls(device, timeout=self.config.notification_timeout_seconds) as client:
            if not client.is_connected:
                return None

            name = await self._read_text(client, STANDARD_CHARACTERISTICS["device_name"]) or device.name or "Unknown device"
            manufacturer = await self._read_text(client, STANDARD_CHARACTERISTICS["manufacturer_name"])
            model = await self._read_text(client, STANDARD_CHARACTERISTICS["model_number"])
            serial_number = await self._read_text(client, STANDARD_CHARACTERISTICS["serial_number"])

            measurements: List[Measurement] = []
            measurements.extend(await self._read_measurement(client, "temperature_measurement", parse_temperature_measurement))
            measurements.extend(await self._read_measurement(client, "blood_pressure_measurement", parse_blood_pressure_measurement))
            measurements.extend(await self._read_measurement(client, "weight_measurement", parse_weight_measurement))

            battery = await self._read_battery(client)
            if battery is not None:
                measurements.append(battery)

            return DeviceReading(
                address=device.address,
                name=name,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                measurements=measurements,
            )

    async def _read_measurement(self, client, key: str, parser) -> List[Measurement]:
        payload = await self._read_payload(client, STANDARD_CHARACTERISTICS[key])
        if not payload:
            return []

        try:
            return parser(payload)
        except Exception as exc:
            LOGGER.warning("Failed to parse %s: %s", key, exc)
            return []

    async def _read_payload(self, client, uuid: str) -> Optional[bytes]:
        try:
            return bytes(await client.read_gatt_char(uuid))
        except Exception:
            event = asyncio.Event()
            container: Dict[str, bytes] = {}

            def callback(_, data: bytearray) -> None:
                container["payload"] = bytes(data)
                event.set()

            try:
                await client.start_notify(uuid, callback)
                await asyncio.wait_for(event.wait(), timeout=self.config.notification_timeout_seconds)
                return container.get("payload")
            except Exception:
                return None
            finally:
                try:
                    await client.stop_notify(uuid)
                except Exception:
                    pass

    async def _read_text(self, client, uuid: str) -> Optional[str]:
        payload = await self._read_payload(client, uuid)
        if not payload:
            return None

        return payload.decode("utf-8", errors="ignore").strip() or None

    async def _read_battery(self, client) -> Optional[Measurement]:
        payload = await self._read_payload(client, STANDARD_CHARACTERISTICS["battery_level"])
        if not payload:
            return None

        return Measurement(
            code="battery-level",
            display="Battery level",
            value=float(payload[0]),
            unit="%",
            system="http://unitsofmeasure.org",
            unit_code="%",
            code_system="https://hub.io/fhir/CodeSystem/device-metrics",
        )

    def _mock_readings(self) -> List[DeviceReading]:
        return [
            DeviceReading(
                address="00:11:22:33:44:55",
                name="Mock BP Monitor",
                manufacturer="Hub.io",
                model="Mock-BPM-1",
                serial_number="MOCK123",
                measurements=parse_blood_pressure_measurement(bytes([0x04, 0x76, 0x00, 0x4C, 0x00, 0x5E, 0x00, 0x48, 0x00])),
            ),
            DeviceReading(
                address="AA:BB:CC:DD:EE:FF",
                name="Mock Thermometer",
                manufacturer="Hub.io",
                model="Mock-TEMP-1",
                serial_number="MOCK456",
                measurements=parse_temperature_measurement(bytes([0x00, 0xED, 0x0E, 0x00, 0xFE])),
            ),
        ]
