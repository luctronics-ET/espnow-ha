
#ifndef ESPNOW_PROTOCOL_H
#define ESPNOW_PROTOCOL_H

#include <stdint.h>

#define PKT_HELLO 1
#define PKT_SENSOR 2
#define PKT_HEARTBEAT 3
#define PKT_COMMAND 4

typedef struct {

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

} espnow_packet_t;

#endif
