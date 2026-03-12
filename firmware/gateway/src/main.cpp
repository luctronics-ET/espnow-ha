/*
 * Aguada Gateway Firmware v3.2
 * ESP32-S3
 *
 * Receives ESP-NOW → outputs JSON lines on USB Serial 115200bps
 * Reads JSON commands from USB Serial → sends ESP-NOW to nodes
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_timer.h>
#include <esp_log.h>
#include <ArduinoJson.h>
#include <string.h>

#include "espnow_gw.h"
#include "../../shared/protocol.h"

static const char *TAG = "gw";

// ── Timestamp ─────────────────────────────────────────────────────────────────
// No WiFi/NTP on gateway. bridge.py sends {"cmd":"SETTIME","ts":...} at startup.
static int64_t s_time_offset_s = 0;

static uint32_t unix_now(void) {
    return (uint32_t)(s_time_offset_s + esp_timer_get_time() / 1000000LL);
}

// ── Node MAC cache ────────────────────────────────────────────────────────────
#define NODE_CACHE_MAX 20
typedef struct { uint16_t node_id; uint8_t mac[6]; } node_mac_t;
static node_mac_t s_nodes[NODE_CACHE_MAX];
static int s_nodes_len = 0;

static void cache_mac(uint16_t node_id, const uint8_t *mac) {
    for (int i = 0; i < s_nodes_len; i++) {
        if (s_nodes[i].node_id == node_id) { memcpy(s_nodes[i].mac, mac, 6); return; }
    }
    if (s_nodes_len < NODE_CACHE_MAX) {
        s_nodes[s_nodes_len].node_id = node_id;
        memcpy(s_nodes[s_nodes_len].mac, mac, 6);
        s_nodes_len++;
    }
}

static const uint8_t *find_mac(uint16_t node_id) {
    for (int i = 0; i < s_nodes_len; i++)
        if (s_nodes[i].node_id == node_id) return s_nodes[i].mac;
    return nullptr;
}

// ── JSON output helpers ───────────────────────────────────────────────────────

static void json_out(JsonDocument &doc) {
    serializeJson(doc, Serial);
    Serial.println();
}

static void output_sensor(const espnow_packet_t *pkt) {
    JsonDocument doc;
    char nid[8]; snprintf(nid, sizeof(nid), "0x%04X", pkt->node_id);
    doc["v"]           = 3;
    doc["type"]        = "SENSOR";
    doc["node_id"]     = nid;
    doc["sensor_id"]   = pkt->sensor_id;
    doc["distance_cm"] = (pkt->flags & FLAG_SENSOR_ERROR) ? -1 : (int)pkt->distance_cm;
    doc["rssi"]        = pkt->rssi;
    doc["vbat"]        = pkt->vbat;
    doc["flags"]       = pkt->flags;
    doc["seq"]         = pkt->seq;
    doc["ts"]          = unix_now();
    json_out(doc);
}

static void output_heartbeat(const espnow_packet_t *pkt) {
    JsonDocument doc;
    char nid[8]; snprintf(nid, sizeof(nid), "0x%04X", pkt->node_id);
    doc["v"]         = 3;
    doc["type"]      = "HEARTBEAT";
    doc["node_id"]   = nid;
    doc["sensor_id"] = pkt->sensor_id;
    doc["rssi"]      = pkt->rssi;
    doc["seq"]       = pkt->seq;
    doc["ts"]        = unix_now();
    json_out(doc);
}

static void output_hello(const espnow_packet_t *pkt) {
    JsonDocument doc;
    char nid[8]; snprintf(nid, sizeof(nid), "0x%04X", pkt->node_id);
    doc["v"]           = 3;
    doc["type"]        = "HELLO";
    doc["node_id"]     = nid;
    doc["fw_version"]  = FW_VERSION;
    // distance_cm reused to carry num_sensors in HELLO
    doc["num_sensors"] = pkt->distance_cm;
    doc["ts"]          = unix_now();
    json_out(doc);
}

// ── ESP-NOW receive ───────────────────────────────────────────────────────────

static void on_recv(const espnow_packet_t *pkt, const uint8_t *src_mac) {
    cache_mac(pkt->node_id, src_mac);

    switch (pkt->type) {
        case PKT_SENSOR:    output_sensor(pkt);    break;
        case PKT_HEARTBEAT: output_heartbeat(pkt); break;
        case PKT_HELLO:     output_hello(pkt);     break;
        default:
            ESP_LOGW(TAG, "Unhandled type=0x%02X from 0x%04X", pkt->type, pkt->node_id);
            break;
    }
}

// ── Command → ESP-NOW ─────────────────────────────────────────────────────────

static void cmd_restart(uint16_t node_id) {
    const uint8_t *mac = find_mac(node_id);
    if (!mac) { ESP_LOGW(TAG, "No MAC for 0x%04X", node_id); return; }

    espnow_packet_t pkt = {};
    pkt.version = PROTO_VERSION;
    pkt.type    = PKT_CMD_RESTART;
    pkt.node_id = node_id;
    pkt.ttl     = DEFAULT_TTL;
    gw_espnow_send(&pkt, mac);
    ESP_LOGI(TAG, "CMD_RESTART → 0x%04X", node_id);
}

static void cmd_config(uint16_t node_id, const JsonDocument &doc) {
    const uint8_t *mac = find_mac(node_id);
    if (!mac) { ESP_LOGW(TAG, "No MAC for 0x%04X", node_id); return; }

    espnow_packet_t pkt = {};
    pkt.version = PROTO_VERSION;
    pkt.type    = PKT_CMD_CONFIG;
    pkt.node_id = node_id;
    pkt.ttl     = DEFAULT_TTL;
    pkt.flags   = FLAG_CONFIG_PENDING;
    gw_espnow_send(&pkt, mac);
    ESP_LOGI(TAG, "CMD_CONFIG → 0x%04X", node_id);
    (void)doc;
}

// ── Serial command parser ─────────────────────────────────────────────────────

static char   s_buf[512];
static size_t s_buf_len = 0;

static void process_cmd(const char *str) {
    JsonDocument doc;
    if (deserializeJson(doc, str) != DeserializationError::Ok) {
        ESP_LOGW(TAG, "Bad JSON: %.80s", str);
        return;
    }

    const char *cmd = doc["cmd"];
    if (!cmd) return;

    if (strcmp(cmd, "SETTIME") == 0) {
        int64_t ts = doc["ts"].as<int64_t>();
        s_time_offset_s = ts - (esp_timer_get_time() / 1000000LL);
        ESP_LOGI(TAG, "Time set, unix_now=%u", unix_now());
        return;
    }

    uint16_t node_id = 0;
    if (doc["node_id"].is<const char*>())
        node_id = (uint16_t)strtoul(doc["node_id"].as<const char*>(), nullptr, 0);
    else
        node_id = doc["node_id"].as<uint16_t>();

    if      (strcmp(cmd, "RESTART") == 0) cmd_restart(node_id);
    else if (strcmp(cmd, "CONFIG")  == 0) cmd_config(node_id, doc);
    else ESP_LOGW(TAG, "Unknown cmd: %s", cmd);
}

static void serial_tick(void) {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (s_buf_len > 0) {
                s_buf[s_buf_len] = '\0';
                process_cmd(s_buf);
                s_buf_len = 0;
            }
        } else if (s_buf_len < sizeof(s_buf) - 1) {
            s_buf[s_buf_len++] = c;
        }
    }
}

// ── Setup / Loop ──────────────────────────────────────────────────────────────

void setup(void) {
    Serial.begin(115200);
    delay(300);

    gw_espnow_init(ESPNOW_CHANNEL, on_recv);

    uint8_t mac[6];
    WiFi.macAddress(mac);

    JsonDocument doc;
    char mac_str[20];
    snprintf(mac_str, sizeof(mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    doc["v"]    = 3;
    doc["type"] = "GATEWAY_READY";
    doc["fw"]   = FW_VERSION;
    doc["mac"]  = mac_str;
    doc["ts"]   = 0;
    json_out(doc);
}

void loop(void) {
    serial_tick();
    delay(5);
}
