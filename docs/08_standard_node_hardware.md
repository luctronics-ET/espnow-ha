# Standard Node Hardware Design

## Objectives

Create a universal node board compatible with:

-   ESP32-C3
-   ESP32-S3
-   ESP32 DevKit modules

## Core Components

ESP32 module

Power supply: 5V input 3.3V regulator

## Interfaces

I2C connector

Used for:

temperature sensors pressure sensors lux sensors

SPI connector

Used for:

displays ADC expanders

UART connector

For debugging or external modules.

## GPIO Expansion

Expose at least:

8 GPIO 2 ADC 1 PWM

## Sensor Connectors

Recommended:

Qwiic / STEMMA QT

Advantages:

plug-and-play sensors no soldering

## Antenna

IPEX connector recommended.

Benefits:

external antenna better range flexible mounting

## Example Node Configuration

Reservoir sensor node:

ESP32-C3 ultrasonic sensor SHT31 temperature/humidity

Relay node:

ESP32 DevKit external antenna environment sensors

Gateway node:

ESP32-S3 USB OLED display buzzer buttons
