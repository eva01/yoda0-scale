# Raspberry Pi Setup

This project should work on Raspberry Pi through Bleak's Linux BlueZ backend.

## Recommended Hardware

- Raspberry Pi 4, 5, or Zero 2 W
- Raspberry Pi OS Bookworm or newer
- Built-in Bluetooth or a USB BLE adapter

## System Packages

```bash
sudo apt update
sudo apt install -y bluetooth bluez python3-dbus
sudo systemctl enable --now bluetooth
```

Check the adapter:

```bash
bluetoothctl show
```

If Bluetooth is blocked:

```bash
rfkill list bluetooth
sudo rfkill unblock bluetooth
bluetoothctl power on
```

## Install Project

```bash
uv sync
```

## Test Live Reading

Put the scale near the Pi and wake it.

```bash
uv run yoda0-scale read --json --seconds 45
```

Expected output:

```json
{"device_id":"...","loaded":true,"payload":"C0091D4C1388000025000000000000","raw_weight":7500,"rssi":-52,"sequence":9,"timestamp":"...","weight_kg":75.0}
```

## Capture For Debugging

```bash
uv run yoda0-scale capture --seconds 45 --out captures/pi-test.ndjson
uv run yoda0-scale decode captures/pi-test.ndjson --all
```

## Notes

- BLE advertisements are short-lived. Keep the scale awake during capture.
- If `read` returns no measurement, try `capture` first to verify packets are arriving.
- On headless Linux, Bluetooth permission behavior varies by distro. Running under a normal user may need extra D-Bus or bluetooth group setup.
