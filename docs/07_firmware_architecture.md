# ESP32 Universal Firmware Architecture

## Goal

Create a single firmware that supports:

-   sensor nodes
-   relay nodes
-   USB gateways

Configuration determines behavior.

## Module Layout

radio/ mesh/ drivers/ config/ ota/ gateway/ ui/

## Radio Module

Handles:

-   ESP-NOW TX/RX
-   packet queue
-   channel configuration

## Mesh Module

Responsibilities:

-   neighbor table
-   routing decisions
-   packet forwarding

## Drivers Module

Sensor drivers:

ultrasonic sht31 bme280 adc gpio

Each driver implements:

init() read() status()

## Config Module

Stores node configuration in NVS.

Example configuration:

node_id sensor list GPIO assignments

## OTA Module

Handles:

-   firmware block reception
-   flash writing
-   checksum validation
-   reboot

## Gateway Module

Enabled when USB detected.

Functions:

-   publish MQTT
-   diagnostics
-   OTA control

## UI Module

Optional local interface:

display buzzer buttons LEDs
