
# Sensor Driver API

Drivers must implement:

struct SensorDriver {

 const char* name;

 bool (*init)();

 bool (*detect)();

 bool (*read)(int32_t* v1, int32_t* v2);

 uint32_t default_interval;

};

Example:

Ultrasonic driver

value1 = water level
value2 = raw distance
