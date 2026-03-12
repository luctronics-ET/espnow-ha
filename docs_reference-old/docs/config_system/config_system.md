
# Configuration System

Configuration stored in ESP32 NVS.

## NodeConfig

struct NodeConfig {

 uint16_t node_id;

 uint8_t role;

 uint32_t sample_interval;

};

Roles:

0 sensor
1 relay
2 gateway

## Configuration Methods

Priority order:

1 BLE configuration
2 Serial CLI
3 OTA config packet
4 default firmware config

## BLE Configuration

Mobile app connects and sets:

node_id
sensor type
GPIO assignments
sampling intervals
