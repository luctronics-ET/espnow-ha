
struct Neighbor{

uint8_t id;
int rssi;
uint8_t hop;
uint32_t last_seen;

};

Neighbor neighbors[12];

void updateNeighbor(uint8_t id,int rssi,uint8_t hop){

for(int i=0;i<12;i++){

if(neighbors[i].id==id || neighbors[i].id==0){

neighbors[i].id=id;
neighbors[i].rssi=rssi;
neighbors[i].hop=hop;
neighbors[i].last_seen=millis();

return;
}
}
}

int bestRoute(){

int best=-999;
int bestNode=-1;

for(int i=0;i<12;i++){

int score = neighbors[i].rssi - (neighbors[i].hop*10);

if(score>best){

best=score;
bestNode=neighbors[i].id;

}
}

return bestNode;
}
