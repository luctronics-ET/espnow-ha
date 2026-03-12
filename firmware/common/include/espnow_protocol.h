
#ifndef ESPNOW_PROTOCOL_H
#define ESPNOW_PROTOCOL_H

#include <stdint.h>

#define PKT_HELLO 1
#define PKT_SENSOR 2
#define PKT_HEARTBEAT 3
#define PKT_COMMAND 4
#define PKT_OTA_BLOCK 5
#define PKT_OTA_END 6
#define PKT_ACK 7

typedef struct {

uint8_t version;
uint8_t type;

uint8_t src;
uint8_t dst;

uint8_t ttl;

uint32_t seq;
uint32_t timestamp;

int16_t value1;
int16_t value2;

uint16_t crc;

} espnow_packet_t;

#endif
