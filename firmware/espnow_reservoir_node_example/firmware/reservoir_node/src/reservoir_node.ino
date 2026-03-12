
#include <WiFi.h>
#include <esp_now.h>

#define TRIG_PIN 0
#define ECHO_PIN 1

uint8_t broadcastAddr[]={0xff,0xff,0xff,0xff,0xff,0xff};

typedef struct {
  uint8_t node;
  int16_t level_cm;
  int16_t temp_c;
} reservoir_packet;

reservoir_packet pkt;

long measureDistance(){

  digitalWrite(TRIG_PIN,LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN,HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN,LOW);

  long duration=pulseIn(ECHO_PIN,HIGH,30000);

  long distance=duration*0.034/2;

  return distance;
}

void sendPacket(){

  pkt.level_cm=measureDistance();

  pkt.temp_c=random(20,30); // placeholder for SHT31

  esp_now_send(broadcastAddr,(uint8_t*)&pkt,sizeof(pkt));

}

void onReceive(const esp_now_recv_info *info,const uint8_t *data,int len){

  // simple relay
  if(len>0){
    esp_now_send(broadcastAddr,data,len);
  }

}

void setup(){

  Serial.begin(115200);

  pinMode(TRIG_PIN,OUTPUT);
  pinMode(ECHO_PIN,INPUT);

  WiFi.mode(WIFI_STA);

  esp_now_init();

  esp_now_peer_info_t peerInfo={};
  memcpy(peerInfo.peer_addr,broadcastAddr,6);
  peerInfo.channel=0;
  peerInfo.encrypt=false;

  esp_now_add_peer(&peerInfo);

  esp_now_register_recv_cb(onReceive);

  pkt.node=1;

}

void loop(){

  sendPacket();

  Serial.println("Reservoir data sent");

  delay(30000);

}
