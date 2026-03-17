#pragma once
#include <stdint.h>
#include <assert.h>

// Protocol version
#define PROTO_VERSION       0x03
#define ESPNOW_CHANNEL      1
#define FW_VERSION          "4.0.0"

// Defaults (used by both node and gateway)
#define DEFAULT_MEASURE_S       30
#define DEFAULT_SEND_S          120
#define DEFAULT_HEARTBEAT_S     60
#define DEFAULT_FILTER_WINDOW   5
#define DEFAULT_OUTLIER_CM      10
#define DEFAULT_THRESHOLD_CM    2
#define DEFAULT_TTL             8
#define VBAT_LOW_THRESHOLD      32
#define HC_MAX_RANGE_CM         400

// Packet types
#define PKT_SENSOR          0x01
#define PKT_HEARTBEAT       0x02
#define PKT_HELLO           0x03
#define PKT_CMD_CONFIG      0x10
#define PKT_CMD_RESTART     0x11
#define PKT_CMD_OTA_START   0x12
#define PKT_OTA_BLOCK       0x13
#define PKT_OTA_END         0x14
#define PKT_ACK             0x20

// Flags bitmask
#define FLAG_IS_RELAY       (1 << 0)
#define FLAG_OTA_PENDING    (1 << 1)
#define FLAG_SENSOR_ERROR   (1 << 2)
#define FLAG_LOW_BATTERY    (1 << 3)
#define FLAG_CONFIG_PENDING (1 << 4)

#define DISTANCE_ERROR      0xFFFF

typedef struct __attribute__((packed)) {
    uint8_t  version;       // 0x03
    uint8_t  type;          // PKT_*
    uint16_t node_id;       // 2 last MAC bytes
    uint8_t  sensor_id;     // 1 or 2 | 0=control/heartbeat
    uint8_t  ttl;           // decremented by relays
    uint16_t seq;           // per-node counter, wraps OK
    uint16_t distance_cm;   // filtered reading | 0xFFFF=error
    int8_t   rssi;          // filled by receiver
    int8_t   vbat;          // tenths of V (33=3.3V) | -1=n/a
    uint8_t  flags;
    uint8_t  reserved;
    uint16_t crc;           // CRC-16/CCITT over bytes 0..13
} espnow_packet_t;          // 16 bytes

static_assert(sizeof(espnow_packet_t) == 16, "Packet must be 16 bytes");
