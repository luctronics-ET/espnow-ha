
struct Neighbor{

uint8_t id;
int rssi;
uint8_t hop;
uint32_t last_seen;

};

Neighbor neighbors[10];

void updateNeighbor(uint8_t id,int rssi,uint8_t hop){

for(int i=0;i<10;i++){

if(neighbors[i].id==id || neighbors[i].id==0){

neighbors[i].id=id;
neighbors[i].rssi=rssi;
neighbors[i].hop=hop;
neighbors[i].last_seen=millis();

return;
}
}
}
