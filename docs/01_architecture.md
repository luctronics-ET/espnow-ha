# ESP‑NOW Sensor Network Architecture

## Goal

Create a scalable sensor/actuator network using ESP32 devices
communicating via ESP‑NOW, with a USB gateway connected to a server
(Home Assistant or other automation systems).

## High Level Architecture

Server (Home Assistant) │ │ USB │ ESP32‑S3 Gateway │ ESP‑NOW │ Multi‑hop
mesh │ ESP32 nodes (sensors / relays / actuators)

## Node Roles

Sensor node - reads sensors - deep sleep possible

Relay node - always powered - forwards packets

Gateway - connected via USB - publishes data to MQTT

## Hardware Types

Short distance nodes ESP32‑C3 SuperMini

Long distance nodes ESP32 DevKit with external antenna

Gateway ESP32‑S3 with USB + display

## Key Features

-   OTA firmware updates
-   mesh multi‑hop routing
-   automatic device discovery
-   MQTT integration
