# Captures

Raw `.ndjson` captures are useful for local debugging but should not be committed.

Each line is one BLE advertisement record:

```json
{"id":"...","manufacturerData":"C0091D4C1388000025000000000000","name":"Yoda0","rssi":-52,"serviceData":{},"services":[],"timestamp":"..."}
```

Decode a capture:

```bash
uv run yoda0-scale decode captures/session.ndjson --all
```
