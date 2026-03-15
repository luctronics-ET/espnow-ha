#pragma once
#include <stdbool.h>
#include "protocol.h"   // shared: FW_VERSION, defaults, packet types

#define NVS_NAMESPACE           "aguada"
#define OTA_BLOCK_SIZE          200

typedef struct {
    uint8_t trig_pin;
    uint8_t echo_pin;
    bool    enabled;
} sensor_hw_t;

typedef struct {
    uint16_t    node_id;                // 2 last MAC bytes
    uint8_t     num_sensors;            // 0=relay, 1 or 2
    sensor_hw_t sensor[2];             // [0]=sensor_id1, [1]=sensor_id2

    // Timing
    uint16_t    interval_measure_s;
    uint16_t    interval_send_s;
    uint16_t    heartbeat_s;

    // Filters
    uint8_t     filter_window;
    uint8_t     filter_outlier_cm;
    uint8_t     filter_threshold_cm;

    // Optional features
    bool        vbat_enabled;
    uint8_t     vbat_pin;
    bool        deep_sleep_enabled;
    bool        led_enabled;

    // Network
    uint8_t     espnow_channel;
    uint8_t     ttl_max;

    // Maintenance
    uint8_t     restart_daily_h;        // 0=disabled
    char        fw_version[8];
} node_config_t;

// GPIO defaults for ESP32-C3 SuperMini
#define DEFAULT_TRIG1   1
#define DEFAULT_ECHO1   0
#define DEFAULT_TRIG2   3
#define DEFAULT_ECHO2   2
#define DEFAULT_LED_PIN 8               // active-low
