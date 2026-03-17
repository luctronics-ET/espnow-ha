---
description: "Use when working on ESP32 firmware (ESP32-C3/ESP32-S3), ESP-NOW packet flow, USB serial bridge, MQTT bridge logic, or OTA transport/update reliability."
name: "ESP32 ESP-NOW Serial Bridge OTA"
applyTo: "firmware/**/*.h, firmware/**/*.cpp, firmware/**/*.ino, tools/bridge.py, tools/**/*.py, tools/**/*.sh"
---
# ESP32 + ESP-NOW + Serial Bridge + OTA Guidelines

- Prefer `AGUADA_SYSTEM_DOC.md` as the primary source for protocol, packet layout, config model, and reservoir calculations.
- Preserve protocol v3 compatibility:
  - Keep packet struct packed and fixed-size.
  - Keep CRC-16/CCITT validation on bytes `0..13` and avoid bypassing CRC checks in production code.
  - Keep `version=0x03` behavior explicit.

- Keep node/gateway responsibilities separated:
  - Node sends measurement primitives (`distance_cm`, telemetry metadata).
  - Bridge computes reservoir-level metrics (`level_cm`, `%`, `volume_L`) using `tools/reservoirs.yaml`.

- For ESP-NOW receive callbacks on ESP32:
  - Prefer avoiding heavy work, dynamic JSON serialization, or USB serial writes inside WiFi/ESP-NOW callback context.
  - Prefer pushing received data to queue/ring buffer and processing in main loop/task.

- Serial bridge robustness:
  - Emit one complete JSON object per line.
  - Avoid partial writes and mixed binary/text output on the same channel.
  - When changing message format, update both firmware producer and `tools/bridge.py` parser together.

- Relay/mesh forwarding safety:
  - Prefer decrementing TTL exactly once per hop and dropping packets when TTL reaches zero.
  - Keep dedup keys collision-resistant (include both `node_id` and sequence identity).
  - Prefer not forwarding packets back to the immediate source peer.

- NVS/config changes:
  - Maintain backward-safe defaults for new fields.
  - Keep remote config parsing deterministic and flag-gated.
  - Validate ranges for pins, intervals, ADC/divider values before persisting.

- OTA transport/update rules:
  - Prioritize OTA block ordering and integrity checks (CRC/consistency) as first-class validation.
  - Prefer requiring positive completion criteria (`OTA_END` + integrity pass) before switching image.
  - Prioritize preserving a recovery path (safe restart + previous image fallback behavior when supported).

- Validation before finalizing changes:
  - Build affected firmware target(s) and verify no new compile warnings/errors in changed modules.
  - Verify bridge path with real serial logs and JSON parsing when changing gateway or bridge code.
  - For protocol/config changes, validate at least one end-to-end flow: node -> gateway -> serial -> bridge -> MQTT.
