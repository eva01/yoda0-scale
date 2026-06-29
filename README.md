# Yoda0 Bluetooth Scale CLI

Read weight measurements from a `Yoda0` Bluetooth scale using BLE advertisements.

This project was built from live captures of a Yoda0 scale. The scale broadcasts the weight in manufacturer data; it does not need a GATT connection for the basic reading path.

## Status

- Confirmed device name: `Yoda0`
- Example live reading: `75.00 kg`
- Confirmed payload format:
  - byte `0`: packet prefix, `C0`
  - byte `1`: sequence/counter
  - bytes `2-3`: big-endian centi-kg
  - byte `8`: load flag, `0x24` = no load, `0x25` = loaded reading

Example:

```text
C0091D4C1388000025000000000000
     ^^^^
0x1D4C = 7500 / 100 = 75.00 kg
```

## Install

Use `uv`:

```bash
uv sync
```

Or install in editable mode:

```bash
uv pip install -e .
```

## CLI

Check runtime dependencies:

```bash
uv run yoda0-scale doctor
```

Read a live loaded measurement:

```bash
uv run yoda0-scale read
```

Print JSON:

```bash
uv run yoda0-scale read --json
```

Capture raw advertisements:

```bash
uv run yoda0-scale capture --seconds 30 --out captures/session.ndjson
```

Decode a capture:

```bash
uv run yoda0-scale decode captures/session.ndjson
```

Include unloaded zero packets while decoding:

```bash
uv run yoda0-scale decode captures/session.ndjson --all
```

## Raspberry Pi

See [docs/raspberry-pi.md](docs/raspberry-pi.md).

Short version:

```bash
sudo apt update
sudo apt install -y bluetooth bluez python3-dbus
sudo systemctl enable --now bluetooth
uv sync
uv run yoda0-scale doctor
uv run yoda0-scale read --json
```

If scanning fails on Linux, check permissions and adapter state:

```bash
bluetoothctl show
bluetoothctl power on
rfkill list bluetooth
```

## macOS Fallback Scanner

The main CLI uses Python/Bleak. A native CoreBluetooth scanner is kept in [tools/macos-swift/ble-capture.swift](tools/macos-swift/ble-capture.swift) because it was useful during initial reverse engineering.

Build it:

```bash
mkdir -p /tmp/yoda0-swift-module-cache
swiftc -module-cache-path /tmp/yoda0-swift-module-cache tools/macos-swift/ble-capture.swift -o ble-capture
```

Run it:

```bash
./ble-capture --seconds 20 --name Yoda0 --min-rssi -90
```

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

The decoder is intentionally pure Python and hardware-free so protocol changes can be tested without a scale nearby.
