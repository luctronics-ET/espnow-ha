# Device Descriptor Model

Nodes describe their capabilities to the gateway.

Example descriptor:

{ "node_id":3, "name":"reservatorio_1", "sensors":\[ {
"type":"ultrasonic", "trig":0, "echo":1 }, { "type":"sht31",
"i2c_addr":"0x44" } \] }

Gateway converts descriptor into MQTT entities.
