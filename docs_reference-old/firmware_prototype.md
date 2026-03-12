# Minimal ESP‑NOW Firmware Prototype

This firmware demonstrates a minimal working node and gateway.

## Node Responsibilities

-   read sensors
-   transmit packets
-   receive commands
-   optional relay

## Basic Firmware Structure

src/

radio/\
mesh/\
sensors/\
config/\
ota/\
gateway/\
ui/

## Node Pseudocode

loop {

    readSensors();

    sendPacket();

    delay(60000);

}

## ESP‑NOW Transmission Example

esp_now_send( gateway_mac, (uint8_t\*)&packet, sizeof(packet) );

## Example Packet Creation

packet.src = node_id; packet.type = SENSOR; packet.value1 = distance_cm;

## Gateway Firmware Concept

Gateway receives ESP‑NOW packets and sends them to the server.

Flow:

ESP‑NOW RX\
↓\
queue\
↓\
USB serial\
↓\
Home Assistant

## Example USB Output

N3 LEVEL=182 RSSI=-64

or JSON:

{ "node":3, "level":182, "rssi":-64 }

## Python Example Gateway Bridge

Example reading USB and publishing MQTT:

import serial

ser = serial.Serial("/dev/ttyACM0",115200)

while True: line = ser.readline() print(line)

## OTA Concept

Firmware updates are distributed through the mesh.

Flow:

Gateway\
↓\
ESP‑NOW\
↓\
Relay nodes\
↓\
Target node

Firmware blocks (\~200 bytes) are transmitted sequentially.

Typical update time: 10‑30 seconds.

## Development Cycle

1.  Write code
2.  OTA upload
3.  Test
4.  Improve
5.  OTA again

USB is only required for the first flash.
