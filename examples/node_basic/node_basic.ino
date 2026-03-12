
#include <Arduino.h>
#include "../../framework/api/framework_api.h"

int readFakeSensor(){

return random(100,200);

}

void setup(){

Serial.begin(115200);

frameworkInit();

}

void loop(){

int value=readFakeSensor();

meshSendSensor(value,25);

delay(5000);

}
