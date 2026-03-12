# ESP‑NOW Network Protocol Specification

## Packet Structure

struct packet { uint8_t version; uint8_t type; uint8_t src; uint8_t dst;
uint8_t ttl; uint32_t seq; uint32_t timestamp; uint8_t payload\[16\];
uint16_t crc; };

## Packet Types

HELLO SENSOR_DATA HEARTBEAT COMMAND OTA_BLOCK ACK

## Routing

Each node maintains neighbor table:

node_id RSSI hop_to_gateway

Routing metric:

score = RSSI - (hop \* 10)

Highest score chosen.

## Loop Prevention

Nodes store recent packets:

src + seq

Duplicate packets ignored.
