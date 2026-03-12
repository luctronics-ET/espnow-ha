
int readUltrasonic(int trig,int echo){

    digitalWrite(trig,LOW);
    delayMicroseconds(2);

    digitalWrite(trig,HIGH);
    delayMicroseconds(10);

    digitalWrite(trig,LOW);

    long duration = pulseIn(echo,HIGH);

    int distance = duration * 0.034 / 2;

    return distance;
}
