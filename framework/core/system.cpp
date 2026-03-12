
#include <WiFi.h>
#include <esp_now.h>
#include "../protocol/espnow_protocol.h"

uint8_t broadcastAddr[]={0xff,0xff,0xff,0xff,0xff,0xff};

void frameworkInit(){

WiFi.mode(WIFI_STA);

if(esp_now_init()!=ESP_OK){
Serial.println("ESP-NOW init failed");
}

esp_now_peer_info_t peerInfo={};
memcpy(peerInfo.peer_addr,broadcastAddr,6);

esp_now_add_peer(&peerInfo);

}
