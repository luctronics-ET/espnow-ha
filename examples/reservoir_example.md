
# Example Reservoir Node Using Framework API

frameworkInit();

registerSensorDriver(ultrasonic_driver);

loop:

readSensors();

meshSendSensor(level_mm, temperature);
