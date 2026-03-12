
# Device Descriptor

Each node reports capabilities to the gateway.

Example:

{
 "node_id":3,
 "device_type":"sensor_node",
 "sensors":[
   {"type":"ultrasonic","trig":0,"echo":1},
   {"type":"sht31","i2c_addr":"0x44"}
 ]
}

Gateway converts this descriptor into MQTT entities automatically.
