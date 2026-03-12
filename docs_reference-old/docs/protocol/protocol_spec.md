
# ESP-NOW Framework – Definitive Binary Protocol

## Goals

- small packets
- deterministic parsing
- extensible
- mesh-friendly

## Packet Structure

struct packet {

 uint8_t version;
 uint8_t type;

 uint16_t src;
 uint16_t dst;

 uint8_t ttl;
 uint8_t flags;

 uint32_t seq;
 uint32_t timestamp;

 int32_t value1;
 int32_t value2;

 uint16_t crc;

}

Typical size: 24–32 bytes.

## Packet Types

0x01 HELLO
0x02 SENSOR
0x03 HEARTBEAT
0x04 COMMAND
0x05 CONFIG
0x06 OTA_BLOCK
0x07 OTA_END
0x08 ACK

## SENSOR payload

value1 → primary measurement  
value2 → secondary measurement

Example:

value1 = water_level_mm  
value2 = temperature_x100
