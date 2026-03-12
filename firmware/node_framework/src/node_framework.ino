
#include <WiFi.h>
#include <esp_now.h>
#include "espnow_protocol.h"

uint8_t broadcast_addr[] = {0xff,0xff,0xff,0xff,0xff,0xff};

uint32_t seq = 0;

void sendSensor()
{

    espnow_packet_t pkt;

    pkt.version = 1;
    pkt.type = PKT_SENSOR;
    pkt.src = 1;
    pkt.dst = 0;
    pkt.ttl = 5;

    pkt.seq = seq++;
    pkt.timestamp = millis();

    pkt.value1 = random(100,200);
    pkt.value2 = random(20,30);

    esp_now_send(broadcast_addr,(uint8_t*)&pkt,sizeof(pkt));
}

void onReceive(const esp_now_recv_info *info,const uint8_t *data,int len)
{

    espnow_packet_t pkt;
    memcpy(&pkt,data,sizeof(pkt));

    if(pkt.ttl > 0)
    {
        pkt.ttl--;
        esp_now_send(broadcast_addr,(uint8_t*)&pkt,sizeof(pkt));
    }

}

void setup()
{

    Serial.begin(115200);

    WiFi.mode(WIFI_STA);

    if(esp_now_init()!=ESP_OK)
    {
        Serial.println("ESP-NOW init failed");
        return;
    }

    esp_now_peer_info_t peerInfo={};
    memcpy(peerInfo.peer_addr,broadcast_addr,6);
    peerInfo.channel=0;
    peerInfo.encrypt=false;

    esp_now_add_peer(&peerInfo);

    esp_now_register_recv_cb(onReceive);
}

void loop()
{
    sendSensor();
    delay(5000);
}
