from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def read_ndjson(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number}: {error}") from error
            if not isinstance(value, dict):
                raise ValueError(f"Invalid record on line {line_number}: expected object")
            yield value
