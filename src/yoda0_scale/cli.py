from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .bleak_reader import scan_records
from .decoder import decode_manufacturer_data, decode_records
from .records import read_ndjson


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yoda0-scale")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read", help="scan for Yoda0 and print the latest loaded reading")
    read_parser.add_argument("--seconds", type=float, default=30)
    read_parser.add_argument("--name", default="Yoda0")
    read_parser.add_argument("--min-rssi", type=int, default=-90)
    read_parser.add_argument("--json", action="store_true", dest="json_output")

    capture_parser = subparsers.add_parser("capture", help="capture BLE advertisements as NDJSON")
    capture_parser.add_argument("--seconds", type=float, default=30)
    capture_parser.add_argument("--name", default="Yoda0")
    capture_parser.add_argument("--min-rssi", type=int, default=-90)
    capture_parser.add_argument("--out", type=Path)

    decode_parser = subparsers.add_parser("decode", help="decode a capture file")
    decode_parser.add_argument("capture", type=Path)
    decode_parser.add_argument("--all", action="store_true", help="include unloaded zero readings")

    doctor_parser = subparsers.add_parser("doctor", help="check runtime dependencies")
    doctor_parser.set_defaults(func=_doctor)

    args = parser.parse_args(argv)
    if args.command == "read":
        return asyncio.run(_read(args))
    if args.command == "capture":
        return asyncio.run(_capture(args))
    if args.command == "decode":
        return _decode(args)
    if args.command == "doctor":
        return _doctor(args)
    parser.error("unknown command")


async def _read(args: argparse.Namespace) -> int:
    latest = None
    async for record in scan_records(seconds=args.seconds, name=args.name, min_rssi=args.min_rssi):
        reading = decode_manufacturer_data(
            record.manufacturerData,
            rssi=record.rssi,
            timestamp=record.timestamp,
            device_id=record.id,
        )
        if reading and reading.loaded:
            latest = reading

    if latest is None:
        print("No loaded Yoda0 reading found", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(latest.to_dict(), sort_keys=True))
    else:
        print(f"{latest.weight_kg:.2f} kg")
    return 0


async def _capture(args: argparse.Namespace) -> int:
    output = args.out.open("w", encoding="utf-8") if args.out else sys.stdout
    try:
        async for record in scan_records(seconds=args.seconds, name=args.name, min_rssi=args.min_rssi):
            print(record.to_json(), file=output)
    finally:
        if args.out:
            output.close()
    return 0


def _decode(args: argparse.Namespace) -> int:
    readings = list(decode_records(read_ndjson(args.capture), loaded_only=not args.all))
    for reading in readings:
        print(json.dumps(reading.to_dict(), sort_keys=True))
    return 0 if readings else 1


def _doctor(_args: argparse.Namespace) -> int:
    try:
        import bleak  # noqa: F401
    except ImportError:
        print("Bleak: missing")
        print("Install dependencies with: uv sync")
        return 1

    print("Bleak: installed")
    print("Bluetooth permissions and adapters must be checked on the target OS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
