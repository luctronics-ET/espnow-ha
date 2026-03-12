
# Architecture

Nodes communicate via ESP-NOW using a lightweight binary protocol.

Gateway receives packets and forwards them to automation platforms.

Structure:

Node -> Mesh -> Gateway -> MQTT -> Home Assistant

Modules:

mesh/
routing logic

sensors/
drivers + scheduler

ota/
firmware update

config/
node configuration
