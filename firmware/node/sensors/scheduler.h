
typedef struct {

uint8_t id;
uint32_t interval;
uint32_t last_run;

} sensor_task;

sensor_task tasks[6];

void schedulerRun(){

uint32_t now=millis();

for(int i=0;i<6;i++){

if(tasks[i].interval>0 && now-tasks[i].last_run>tasks[i].interval){

tasks[i].last_run=now;

// sensor read callback here

}
}
}
