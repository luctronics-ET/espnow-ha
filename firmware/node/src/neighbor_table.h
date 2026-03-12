
struct Neighbor {

    uint8_t id;
    int rssi;
    uint8_t hop;
    uint32_t last_seen;

};

Neighbor table[10];

void updateNeighbor(uint8_t id,int rssi,uint8_t hop)
{

    for(int i=0;i<10;i++)
    {

        if(table[i].id==id || table[i].id==0)
        {

            table[i].id=id;
            table[i].rssi=rssi;
            table[i].hop=hop;
            table[i].last_seen=millis();

            return;
        }

    }

}
