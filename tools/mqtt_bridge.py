
import serial
import paho.mqtt.publish as publish

ser = serial.Serial("/dev/ttyACM0",115200)

while True:

    line = ser.readline().decode().strip()

    print(line)

    try:
        parts = line.split()
        node = parts[0].split(":")[1]
        v1 = parts[1].split(":")[1]
        v2 = parts[2].split(":")[1]

        topic = f"espnow/node/{node}"
        payload = f'{{"value1":{v1},"value2":{v2}}}'

        publish.single(topic,payload,hostname="localhost")

    except:
        pass
