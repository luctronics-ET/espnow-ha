
#include <WiFi.h>
#include <esp_now.h>
#include "../../framework/protocol/espnow_protocol.h"

void onReceive(const esp_now_recv_info *info,const uint8_t *data,int len){

espnow_packet_t pkt;

memcpy(&pkt,data,sizeof(pkt));

Serial.print("NODE:");
Serial.print(pkt.src);

Serial.print(" VALUE:");
Serial.println(pkt.value1);

}

void setup(){

Serial.begin(115200);

WiFi.mode(WIFI_STA);

esp_now_init();

esp_now_register_recv_cb(onReceive);

}

void loop(){}
