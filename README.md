# Hub.IO Project

Hub.IO now includes a modern Raspberry Pi 4 medical IoT gateway focused on Bluetooth Low Energy biomedical devices, IEEE 11073 decoding, and HL7 FHIR bundle delivery.

## Current architecture

- `Comunicaciones/`: Raspberry Pi communication layer.
  - Legacy code under `libs/` keeps the original Bluegiga/BGAPI implementation.
  - `main.py` is now the Python 3 entrypoint for the modern BLE-to-FHIR gateway.
  - `gateway/` contains BLE capture, IEEE 11073 parsing, FHIR bundle construction, and HTTP delivery.
- `Config_web_BBB/`: legacy Express + Socket.IO web UI used to pair devices and inspect measurements locally.
- `Servidor/`: legacy Node.js backend skeleton.

## Data flow

1. The Raspberry Pi scans nearby BLE biomedical devices.
2. The gateway connects to supported GATT services and reads standard measurement characteristics.
3. Raw payloads are decoded with IEEE 11073 rules for temperature, blood pressure, weight, and battery level.
4. Decoded readings are mapped into HL7 FHIR `Patient`, `Device`, and `Observation` resources.
5. All resources are packaged into a FHIR `Bundle` and posted to a remote health backend.

## Raspberry Pi 4 gateway

### Install

```bash
cd Comunicaciones
python3 -m pip install -r requirements.txt
```

### Configure

Edit `Comunicaciones/config.json`:

- `backend.endpoint_url`: remote FHIR endpoint
- `backend.auth_token`: optional bearer token
- `backend.verify_tls`: keep `true` in production; set `false` only for controlled test environments with self-signed certificates
- `patient`: patient identity used in emitted bundles
- `ble.device_name_prefixes`: optional device name filters
- `ble.device_address_allowlist`: optional MAC allowlist
- `ble.mock_mode`: `true` for local validation without hardware, `false` on Raspberry Pi with BLE enabled

### Run

```bash
cd Comunicaciones
python3 main.py
```

## Validation

```bash
cd Comunicaciones
PYTHONPATH=. python3 -m unittest discover -s tests
```
