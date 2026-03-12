
# System Architecture

## Logical Architecture

Node
 ↓
ESP‑NOW mesh
 ↓
Gateway
 ↓
MQTT
 ↓
Home Assistant

## Node Types

Sensor node
- reads sensors
- sends telemetry

Relay node
- forwards packets
- extends network coverage

Gateway node
- connected to server
- converts ESP-NOW → MQTT

## Gateway Types

USB gateway
- ESP32 connected directly to server

Ethernet gateway
- ESP32 + ENC28J60

Future gateway
- integrated coordinator like Zigbee dongle

