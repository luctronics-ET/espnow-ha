
# Binary Protocol

Example packet:

struct packet {

 uint8_t version;
 uint8_t type;

 uint16_t src;
 uint16_t dst;

 uint8_t ttl;

 uint32_t seq;
 uint32_t timestamp;

 int32_t value1;
 int32_t value2;

 uint16_t crc;

};

Packet types:

HELLO
SENSOR
HEARTBEAT
COMMAND
CONFIG
OTA_BLOCK
OTA_END
ACK

