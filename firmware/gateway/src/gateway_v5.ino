
#include <WiFi.h>
#include <esp_now.h>
#include "../../common/include/espnow_protocol.h"

void onReceive(const esp_now_recv_info *info,const uint8_t *data,int len){

espnow_packet_t pkt;
memcpy(&pkt,data,sizeof(pkt));

Serial.print("NODE:");
Serial.print(pkt.src);

Serial.print(" LEVEL:");
Serial.print(pkt.value1);

Serial.print(" DIST:");
Serial.print(pkt.value2);

Serial.print(" RSSI:");
Serial.println(info->rx_ctrl->rssi);

}

void setup(){

Serial.begin(115200);

WiFi.mode(WIFI_STA);

esp_now_init();

esp_now_register_recv_cb(onReceive);

}

void loop(){}
