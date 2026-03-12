
#include "../protocol/espnow_protocol.h"

extern uint8_t broadcastAddr[];

void meshSendSensor(int32_t v1,int32_t v2){

espnow_packet_t pkt;

pkt.version=1;
pkt.type=PKT_SENSOR;
pkt.src=1;
pkt.dst=0;
pkt.ttl=5;

pkt.seq=millis();
pkt.timestamp=millis();

pkt.value1=v1;
pkt.value2=v2;

esp_now_send(broadcastAddr,(uint8_t*)&pkt,sizeof(pkt));

}
