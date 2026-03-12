
# Sensor Driver API

Drivers must implement the following interface.

struct SensorDriver {

 const char* name;

 bool (*init)();

 bool (*detect)();

 bool (*read)(int32_t* v1, int32_t* v2);

 uint32_t default_interval;

};

Example ultrasonic driver:

bool ultrasonic_init();
bool ultrasonic_detect();
bool ultrasonic_read(int32_t* v1,int32_t* v2);

SensorDriver ultrasonic_driver = {

 "ultrasonic",
 ultrasonic_init,
 ultrasonic_detect,
 ultrasonic_read,
 10000

};
