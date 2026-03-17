/*
 * Aguada Node Firmware v4.0
 * ESP32-C3 SuperMini
 *
 * Single binary: num_sensors=0 → relay mode, num_sensors>=1 → sensor mode
 * All config from NVS. Reservoir math stays on the server.
 * us_dist_cm() backed by NewPing median + percentage calculation.
 * Transmission every 60 seconds.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_timer.h>
#include <esp_log.h>
#include "protocol.h"
#include "node_config.h"
#include "nvs_config.h"
#include "espnow_radio.h"
#include "ultrasonic.h"
#include "ultrasonic_experiments.h"
#include "mesh.h"
#include "crc16.h"

static const char *TAG = "node";

// ── State ────────────────────────────────────────────────────────────────────

static node_config_t g_cfg;
static uint16_t      g_seq = 0;

// Deferred config-save flag — set in ESP-NOW callback, processed in loop()
static volatile bool g_config_save_pending = false;

// Relay mode: track seen seq numbers to avoid re-forwarding duplicates
#define RELAY_SEEN_SIZE 32
static uint32_t s_relay_seen[RELAY_SEEN_SIZE];
static uint8_t  s_relay_seen_idx = 0;

// ── Helpers ───────────────────────────────────────────────────────────────────

static void led_set(bool on) {
    if (!g_cfg.led_enabled) return;
    // GPIO8 is active-low on ESP32-C3 SuperMini
    digitalWrite(DEFAULT_LED_PIN, on ? LOW : HIGH);
}

static void led_blink(int count, int ms) {
    for (int i = 0; i < count; i++) {
        led_set(true);  delay(ms);
        led_set(false); delay(ms);
    }
}

static int8_t read_vbat(void) {
    if (!g_cfg.vbat_enabled) return -1;
    // ADC 12-bit, Vref ~3.3V — average 8 samples for noise reduction
    // vbat_div=1: direct connection; vbat_div=2: equal-resistor voltage divider
    // 4 warm-up reads first: allows ADC sampling capacitor to charge fully,
    // critical when source impedance is high (e.g. 100k–1M resistor divider)
    for (int i = 0; i < 4; i++) { analogRead(g_cfg.vbat_pin); delayMicroseconds(200); }
    int sum = 0;
    for (int i = 0; i < 8; i++) { sum += analogRead(g_cfg.vbat_pin); delayMicroseconds(200); }
    float raw = sum / 8.0f;
    float div = (float)(g_cfg.vbat_div > 0 ? g_cfg.vbat_div : 1);
    float v = (raw / 4095.0f) * 3.3f * div;
    return (int8_t)roundf(v * 10.0f);  // tenths of V, rounded
}

static bool relay_seen(uint16_t node_id, uint16_t seq) {
    uint32_t key = ((uint32_t)node_id << 16) | seq;
    for (int i = 0; i < RELAY_SEEN_SIZE; i++) {
        if (s_relay_seen[i] == key) {
            return true;
        }
    }
    s_relay_seen[s_relay_seen_idx % RELAY_SEEN_SIZE] = key;
    s_relay_seen_idx++;
    return false;
}

// ── Build & send a packet ─────────────────────────────────────────────────────

static void send_packet(uint8_t type, uint8_t sensor_id, uint16_t distance_cm, uint8_t percent) {
    espnow_packet_t pkt = {};
    pkt.version     = PROTO_VERSION;
    pkt.type        = type;
    pkt.node_id     = g_cfg.node_id;
    pkt.sensor_id   = sensor_id;
    pkt.ttl         = g_cfg.ttl_max;
    pkt.seq         = g_seq++;
    pkt.distance_cm = distance_cm;
    pkt.rssi        = 0; // filled by receiver
    pkt.vbat        = read_vbat();
    pkt.flags       = 0;
    pkt.reserved    = percent;

    if (pkt.vbat != -1 && pkt.vbat < VBAT_LOW_THRESHOLD)
        pkt.flags |= FLAG_LOW_BATTERY;

    espnow_send(&pkt);

    led_blink(1, 30);
    ESP_LOGI(TAG, "TX type=0x%02X sid=%d dist=%d seq=%d", type, sensor_id, distance_cm, pkt.seq - 1);
}

static void send_hello(void) {
    espnow_packet_t pkt = {};
    pkt.version     = PROTO_VERSION;
    pkt.type        = PKT_HELLO;
    pkt.node_id     = g_cfg.node_id;
    pkt.sensor_id   = 0;
    pkt.ttl         = g_cfg.ttl_max;
    pkt.seq         = g_seq++;
    pkt.distance_cm = g_cfg.num_sensors;  // reuse field to carry num_sensors in HELLO
    pkt.vbat        = read_vbat();
    espnow_send(&pkt);
    ESP_LOGI(TAG, "TX HELLO node_id=0x%04X num_sensors=%d", g_cfg.node_id, g_cfg.num_sensors);
}

// ── Receive callback ──────────────────────────────────────────────────────────

static void on_recv(const espnow_packet_t *pkt, const uint8_t *src_mac) {
    // Update neighbor table
    mesh_update_neighbor(pkt->node_id, src_mac, pkt->rssi, pkt->ttl);

    // Commands addressed to us
    if (pkt->node_id == g_cfg.node_id || pkt->node_id == 0xFFFF) {
        if (pkt->type == PKT_CMD_RESTART) {
            ESP_LOGI(TAG, "CMD_RESTART received");
            delay(100);
            esp_restart();
        }
        else if (pkt->type == PKT_CMD_CONFIG) {
            ESP_LOGI(TAG, "CMD_CONFIG received, scheduling save...");
            // Gateway encodes vbat config in spare fields:
            //   pkt->sensor_id  → vbat_pin     (0 = don't update)
            //   pkt->reserved   → vbat_enabled  (0=false, 1=true)
            //   pkt->distance_cm → vbat_div     (0 = don't update, 1=direct, 2=÷2 divider)
            if (pkt->sensor_id > 0)
                g_cfg.vbat_pin = pkt->sensor_id;
            g_cfg.vbat_enabled = (pkt->reserved != 0);
            if (pkt->distance_cm > 0 && pkt->distance_cm <= 8)
                g_cfg.vbat_div = (uint8_t)pkt->distance_cm;
            // Defer NVS write to loop() — NVS must not be called from WiFi task
            g_config_save_pending = true;
        }
    }

    // Relay: forward packets from other nodes if TTL > 0 and not already seen
    if (g_cfg.num_sensors == 0) {  // relay mode always relays
        if (pkt->node_id != g_cfg.node_id && pkt->ttl > 0) {
            if (!relay_seen(pkt->node_id, pkt->seq)) {
                espnow_packet_t relay_pkt = *pkt;
                relay_pkt.ttl--;
                relay_pkt.flags |= FLAG_IS_RELAY;
                espnow_send(&relay_pkt);
                ESP_LOGD(TAG, "Relay: 0x%04X seq=%d ttl=%d", pkt->node_id, pkt->seq, relay_pkt.ttl);
            }
        }
    }
}

// ── Sensor loop ───────────────────────────────────────────────────────────────

static void sensor_tick(uint8_t idx) {
    static uint32_t last_read_ms[2] = {0, 0};
    uint32_t now = millis();
    
    // Ler e enviar a cada 60 segundos
    if (now - last_read_ms[idx] < 60000) {
        return;
    }
    last_read_ms[idx] = now;
    
    if (!g_cfg.sensor[idx].enabled) return;

    uint8_t sid = idx + 1;

    // Parâmetros do reservatório (serão configuráveis via NVS no futuro)
    // Por enquanto, valores razoáveis para teste
    uint16_t min_distance = 10;   // sensor_offset em cm
    uint16_t max_distance = 450;  // sensor_offset + level_max
    
    // Fazer medição com mediana de 5 samples
    UltrasonicReading reading = us_dist_cm(
        g_cfg.sensor[idx].trig_pin,
        g_cfg.sensor[idx].echo_pin,
        5,  // 5 samples
        min_distance,
        max_distance
    );
    
    if (reading.valid) {
        Serial.printf("S%d dist: %u cm, %u%%\n", 
                      sid, reading.distance_cm, reading.percent);
        send_packet(PKT_SENSOR, sid, reading.distance_cm, reading.percent);
    } else {
        Serial.printf("S%d dist: ERR\n", sid);
    }
}

// ── Setup ─────────────────────────────────────────────────────────────────────

void setup(void) {
    Serial.begin(115200);
    delay(200);

    // LED init
    if (g_cfg.led_enabled || true) {  // init unconditionally, may not be configured yet
        pinMode(DEFAULT_LED_PIN, OUTPUT);
        led_set(false);
    }

    // Get node_id from MAC — WiFi.mode() must be called before macAddress()
    uint8_t mac[6];
    WiFi.mode(WIFI_STA);
    WiFi.macAddress(mac);
    uint16_t node_id = ((uint16_t)mac[4] << 8) | mac[5];

    ESP_LOGI(TAG, "MAC: %02X:%02X:%02X:%02X:%02X:%02X  node_id=0x%04X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5], node_id);

    // Load config from NVS
    nvs_config_load(&g_cfg, node_id);

    // Init mesh
    mesh_init();

    // Init ESP-NOW
    espnow_init(g_cfg.espnow_channel, on_recv, nullptr);

    if (g_cfg.num_sensors == 0) {
        ESP_LOGI(TAG, "Mode: RELAY");
        led_blink(3, 100);
    } else {
        ESP_LOGI(TAG, "Mode: SENSOR (num_sensors=%d)", g_cfg.num_sensors);

        // Init ultrasonic sensors
        for (int i = 0; i < 2; i++) {
            if (g_cfg.sensor[i].enabled) {
                ultrasonic_init(g_cfg.sensor[i].trig_pin, g_cfg.sensor[i].echo_pin);
                ESP_LOGI(TAG, "  Sensor %d: TRIG=%d ECHO=%d", i+1,
                         g_cfg.sensor[i].trig_pin, g_cfg.sensor[i].echo_pin);
            }
        }
        led_blink(2, 100);
    }

    // Announce on boot
    send_hello();
}

// ── Loop ──────────────────────────────────────────────────────────────────────

void loop(void) {
    // Handle deferred config save (cannot call NVS from ESP-NOW WiFi callback)
    if (g_config_save_pending) {
        g_config_save_pending = false;
        esp_err_t err = nvs_config_save(&g_cfg);
        ESP_LOGI(TAG, "CMD_CONFIG save: vbat_pin=%d vbat_enabled=%d err=%d",
                 g_cfg.vbat_pin, g_cfg.vbat_enabled, (int)err);
        delay(100);
        esp_restart();
    }

    // Sensor tick (se habilitado)
    if (g_cfg.num_sensors > 0) {
        for (uint8_t i = 0; i < 2; i++) {
            sensor_tick(i);
        }
    }
    
    delay(50);
}
