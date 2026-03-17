---
description: "Use when changing gateway JSON output, serial line protocol, bridge parsing, MQTT payload schema, or Home Assistant discovery/state field compatibility."
name: "Serial JSON Schema Compatibility"
applyTo: "firmware/gateway/**/*.h, firmware/gateway/**/*.cpp, firmware/gateway/**/*.ino, tools/bridge.py, tools/**/*.py, homeassistant/**/*.yaml"
---
# Serial JSON + Bridge Schema Compatibility

- Prefer backward-compatible schema evolution for JSON produced by gateway and consumed by `tools/bridge.py`.
- When adding fields, make them optional in parser paths and preserve existing required keys.
- Avoid renaming/removing existing keys unless bridge parser and downstream MQTT/HA mappings are updated in the same change.

- Keep serial framing stable:
  - Emit exactly one JSON object per line.
  - Avoid extra debug prefixes on data lines consumed by parser.
  - Keep UTF-8 text output deterministic and parseable.

- Validate parser robustness:
  - Ignore/skip malformed lines without crashing the bridge loop.
  - Log parse failures with enough context (line preview + reason), without flooding logs.
  - Preserve service continuity when serial stream is noisy or temporarily unavailable.

- Keep MQTT/HA compatibility explicit:
  - If payload shape changes, update publish code and HA discovery/state mapping together.
  - Preserve stable topic naming (`aguada/...`) unless migration is intentionally planned.
  - Prefer additive changes for telemetry fields.

- Before finalizing:
  - Verify at least one real serial JSON sample parses end-to-end.
  - Verify resulting MQTT payload includes expected keys for existing dashboards/automations.
  - Confirm no mixed binary/text output is introduced on the serial channel used by the bridge.
