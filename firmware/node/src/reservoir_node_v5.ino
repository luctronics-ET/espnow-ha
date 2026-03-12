
#include <WiFi.h>
#include <esp_now.h>
#include "../mesh/mesh_manager.h"
#include "../drivers/ultrasonic_driver.cpp"
#include "../../common/include/espnow_protocol.h"

uint8_t broadcastAddr[]={0xff,0xff,0xff,0xff,0xff,0xff};

int trigPin=0;
int echoPin=1;

uint32_t seq=0;
int tankHeight=300;

void sendLevel(){

espnow_packet_t pkt;

int distance = readUltrasonic(trigPin,echoPin);

int level = tankHeight - distance;

pkt.version=1;
pkt.type=PKT_SENSOR;
pkt.src=1;
pkt.dst=0;
pkt.ttl=5;

pkt.seq=seq++;
pkt.timestamp=millis();

pkt.value1=level;
pkt.value2=distance;

esp_now_send(broadcastAddr,(uint8_t*)&pkt,sizeof(pkt));

}

void onReceive(const esp_now_recv_info *info,const uint8_t *data,int len){

espnow_packet_t pkt;
memcpy(&pkt,data,sizeof(pkt));

updateNeighbor(pkt.src,info->rx_ctrl->rssi,pkt.ttl);

if(pkt.ttl>0){

pkt.ttl--;
esp_now_send(broadcastAddr,(uint8_t*)&pkt,sizeof(pkt));

}

}

void setup(){

Serial.begin(115200);

pinMode(trigPin,OUTPUT);
pinMode(echoPin,INPUT);

WiFi.mode(WIFI_STA);

esp_now_init();

esp_now_peer_info_t peerInfo={};
memcpy(peerInfo.peer_addr,broadcastAddr,6);

esp_now_add_peer(&peerInfo);

esp_now_register_recv_cb(onReceive);

}

void loop(){

sendLevel();

delay(10000);

}
