
# ESP-NOW Reservoir Monitoring Node

Example node for water reservoir monitoring.

Hardware (example):

ESP32-C3 SuperMini
Ultrasonic sensor (HC-SR04)
SHT31 temperature/humidity sensor (I2C)

Connections:

Ultrasonic
TRIG -> GPIO0
ECHO -> GPIO1

SHT31
SDA -> GPIO8
SCL -> GPIO9

Function:

- Measure water distance using ultrasonic
- Convert to water level
- Read temperature/humidity
- Send ESP-NOW packet
- Relay packets if needed

Measurement cycle:

measure every 30 s
transmit every 120 s
