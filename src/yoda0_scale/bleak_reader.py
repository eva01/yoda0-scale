from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class AdvertisementRecord:
    timestamp: str
    name: str
    id: str
    rssi: int
    manufacturerData: str
    serviceData: dict[str, str]
    services: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


async def scan_records(
    *,
    seconds: float,
    name: str = "Yoda0",
    min_rssi: int = -90,
) -> AsyncIterator[AdvertisementRecord]:
    try:
        from bleak import BleakScanner
    except ImportError as error:
        raise RuntimeError("Bleak is required for BLE scanning. Install with: uv sync") from error

    queue: asyncio.Queue[AdvertisementRecord] = asyncio.Queue()
    name_filter = name.lower()

    def on_advertisement(device: Any, advertisement_data: Any) -> None:
        device_name = device.name or getattr(advertisement_data, "local_name", None) or "(no name)"
        rssi = int(getattr(advertisement_data, "rssi", getattr(device, "rssi", -127)) or -127)
        if rssi < min_rssi:
            return
        if name_filter and name_filter not in device_name.lower():
            return

        manufacturer_data = _manufacturer_hex(getattr(advertisement_data, "manufacturer_data", {}) or {})
        service_data = {
            str(key): bytes(value).hex().upper()
            for key, value in (getattr(advertisement_data, "service_data", {}) or {}).items()
        }
        services = [str(uuid) for uuid in (getattr(advertisement_data, "service_uuids", []) or [])]
        queue.put_nowait(
            AdvertisementRecord(
                timestamp=datetime.now(UTC).isoformat(),
                name=device_name,
                id=str(device.address),
                rssi=rssi,
                manufacturerData=manufacturer_data,
                serviceData=service_data,
                services=services,
            )
        )

    scanner = BleakScanner(detection_callback=on_advertisement)
    await scanner.start()
    deadline = asyncio.get_running_loop().time() + seconds
    try:
        while True:
            timeout = deadline - asyncio.get_running_loop().time()
            if timeout <= 0:
                break
            try:
                yield await asyncio.wait_for(queue.get(), timeout=timeout)
            except TimeoutError:
                break
    finally:
        await scanner.stop()


def _manufacturer_hex(manufacturer_data: dict[int, bytes | bytearray]) -> str:
    if not manufacturer_data:
        return ""
    company_id, payload = next(iter(manufacturer_data.items()))
    return int(company_id).to_bytes(2, "little").hex().upper() + bytes(payload).hex().upper()
