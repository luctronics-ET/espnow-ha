
# Reservoir Sensor Node

Example configuration:

ESP32-C3
Ultrasonic sensor
Temperature / humidity sensor (SHT31)

Measurements:

distance -> level
temperature
humidity

Level calculation:

level = tank_height - distance

Alarms:

level_low
level_high
