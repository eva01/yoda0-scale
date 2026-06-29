from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Iterator


@dataclass(frozen=True)
class Yoda0Reading:
    weight_kg: float
    loaded: bool
    sequence: int
    raw_weight: int
    rssi: int | None = None
    timestamp: str | None = None
    device_id: str | None = None
    payload: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decode_manufacturer_data(
    manufacturer_data: str,
    *,
    rssi: int | None = None,
    timestamp: str | None = None,
    device_id: str | None = None,
) -> Yoda0Reading | None:
    payload = manufacturer_data.strip().upper()
    if not payload or len(payload) % 2 != 0:
        return None

    try:
        data = bytes.fromhex(payload)
    except ValueError:
        return None

    if len(data) < 9 or data[0] != 0xC0:
        return None

    raw_weight = (data[2] << 8) | data[3]
    loaded = data[8] == 0x25 and raw_weight > 0

    return Yoda0Reading(
        weight_kg=raw_weight / 100,
        loaded=loaded,
        sequence=data[1],
        raw_weight=raw_weight,
        rssi=rssi,
        timestamp=timestamp,
        device_id=device_id,
        payload=payload,
    )


def decode_records(records: Iterable[dict[str, Any]], *, loaded_only: bool = False) -> Iterator[Yoda0Reading]:
    for record in records:
        reading = decode_manufacturer_data(
            str(record.get("manufacturerData", "")),
            rssi=_optional_int(record.get("rssi")),
            timestamp=_optional_str(record.get("timestamp")),
            device_id=_optional_str(record.get("id")),
        )
        if reading is None:
            continue
        if loaded_only and not reading.loaded:
            continue
        yield reading


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None
