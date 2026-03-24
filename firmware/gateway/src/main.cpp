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
#include <esp_wifi.h>
#include <esp_log.h>
#include <ArduinoJson.h>
#include <string.h>

#include <freertos/queue.h>
#include "espnow_gw.h"
#include "../../shared/protocol.h"

static const char *TAG = "gw";

// ── Timestamp ─────────────────────────────────────────────────────────────────
// No WiFi/NTP on gateway. bridge.py sends {"cmd":"SETTIME","ts":...} at startup.
static int64_t s_time_offset_s = 0;

static uint32_t unix_now(void) {
    return (uint32_t)(s_time_offset_s + esp_timer_get_time() / 1000000LL);
}

// ── Packet queue (ESP-NOW cb → loop) ─────────────────────────────────────────
#define PKT_QUEUE_LEN 16
typedef struct { espnow_packet_t pkt; uint8_t src_mac[6]; } pkt_event_t;
static QueueHandle_t s_pkt_queue = nullptr;

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
    Serial.flush();
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
    doc["v"]           = 3;
    doc["type"]        = "HEARTBEAT";
    doc["node_id"]     = nid;
    doc["sensor_id"]   = pkt->sensor_id;
    doc["distance_cm"] = (int)pkt->distance_cm;
    doc["rssi"]        = pkt->rssi;
    doc["vbat"]        = pkt->vbat;
    doc["reserved"]    = pkt->reserved;  // used by SENSOR_ID_ENV: humidity 0-100
    doc["seq"]         = pkt->seq;
    doc["ts"]          = unix_now();
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
    doc["rssi"]        = pkt->rssi;
    doc["vbat"]        = pkt->vbat;
    doc["flags"]       = pkt->flags;  // FLAG_BTN_HELLO=0x40 indicates button press
    doc["ts"]          = unix_now();
    json_out(doc);
}

// ── ESP-NOW receive ───────────────────────────────────────────────────────────

// Called from WiFi/ESP-NOW task — only enqueue, no Serial I/O.
static void on_recv(const espnow_packet_t *pkt, const uint8_t *src_mac) {
    pkt_event_t evt;
    evt.pkt = *pkt;
    memcpy(evt.src_mac, src_mac, 6);
    xQueueSend(s_pkt_queue, &evt, 0);  // non-blocking; drop if full
}

// ── Command → ESP-NOW ─────────────────────────────────────────────────────────
// Commands are sent via broadcast MAC so that nodes can receive them without
// needing to register the gateway as a peer. Only the target node (matching
// node_id in the packet) will process the command.
static const uint8_t BCAST_MAC[6] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};

static void cmd_restart(uint16_t node_id) {
    espnow_packet_t pkt = {};
    pkt.version = PROTO_VERSION;
    pkt.type    = PKT_CMD_RESTART;
    pkt.node_id = node_id;
    pkt.ttl     = DEFAULT_TTL;
    gw_espnow_send(&pkt, BCAST_MAC);
    ESP_LOGI(TAG, "CMD_RESTART → 0x%04X", node_id);
}

static void cmd_config(uint16_t node_id, const JsonDocument &doc) {

    espnow_packet_t pkt = {};
    pkt.version   = PROTO_VERSION;
    pkt.type      = PKT_CMD_CONFIG;
    pkt.node_id   = node_id;
    pkt.ttl       = DEFAULT_TTL;
    pkt.flags     = FLAG_CONFIG_PENDING;

    // Encode vbat config in spare fields (safe for CMD_CONFIG direction):
    //   sensor_id → vbat_pin   (0 = unchanged / disabled)
    //   reserved  → vbat_enabled (0=false, 1=true)
    //   distance_cm low byte  → vbat_div     (0 = unchanged)
    //   distance_cm high byte → num_sensors  (only if FLAG_CFG_NUM_SENSORS is set)
    if (doc["vbat_pin"].is<uint8_t>())
        pkt.sensor_id = doc["vbat_pin"].as<uint8_t>();
    if (doc["vbat_enabled"].is<bool>() || doc["vbat_enabled"].is<int>())
        pkt.reserved  = doc["vbat_enabled"].as<bool>() ? 1 : 0;
    uint8_t cfg_vbat_div = 0;
    if (doc["vbat_div"].is<uint8_t>())
        cfg_vbat_div = doc["vbat_div"].as<uint8_t>();

    uint8_t cfg_num_sensors = 0;
    bool has_num_sensors = false;
    if (doc["num_sensors"].is<uint8_t>() || doc["num_sensors"].is<int>()) {
        int ns = doc["num_sensors"].as<int>();
        if (ns >= 0 && ns <= 2) {
            has_num_sensors = true;
            cfg_num_sensors = (uint8_t)ns;
            pkt.flags |= FLAG_CFG_NUM_SENSORS;
        }
    }

    pkt.distance_cm = ((uint16_t)cfg_num_sensors << 8) | cfg_vbat_div;

    esp_err_t err = gw_espnow_send(&pkt, BCAST_MAC);
    ESP_LOGI(TAG, "CMD_CONFIG → 0x%04X  vbat_pin=%d vbat_enabled=%d vbat_div=%d num_sensors=%d has_ns=%d err=%d",
             node_id, pkt.sensor_id, pkt.reserved, cfg_vbat_div,
             cfg_num_sensors, has_num_sensors ? 1 : 0, (int)err);
}

// ── Serial command parser ─────────────────────────────────────────────────────

static char   s_buf[1024];
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
    // Increase USB CDC RX buffer so large JSON commands (>256 bytes) are not truncated
    Serial.setRxBufferSize(1024);
    delay(300);

    s_pkt_queue = xQueueCreate(PKT_QUEUE_LEN, sizeof(pkt_event_t));
    gw_espnow_init(ESPNOW_CHANNEL, on_recv);

    uint8_t mac[6];
    // esp_wifi_get_mac is reliable right after WiFi.mode(WIFI_STA) in gw_espnow_init
    if (esp_wifi_get_mac(WIFI_IF_STA, mac) != ESP_OK) {
        WiFi.macAddress(mac);  // fallback
    }

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
    // Drain packet queue (filled by ESP-NOW WiFi-task callback).
    pkt_event_t evt;
    while (xQueueReceive(s_pkt_queue, &evt, 0) == pdTRUE) {
        cache_mac(evt.pkt.node_id, evt.src_mac);
        switch (evt.pkt.type) {
            case PKT_SENSOR:    output_sensor(&evt.pkt);    break;
            case PKT_HEARTBEAT: output_heartbeat(&evt.pkt); break;
            case PKT_HELLO:     output_hello(&evt.pkt);     break;
            default:
                ESP_LOGW(TAG, "Unhandled type=0x%02X from 0x%04X",
                         evt.pkt.type, evt.pkt.node_id);
                break;
        }
    }
    serial_tick();
    delay(5);
}
