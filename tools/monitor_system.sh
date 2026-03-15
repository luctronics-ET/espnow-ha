#!/bin/bash
# Monitor Aguada System Status

MQTT_HOST="192.168.0.177"
MQTT_PORT="1883"
MQTT_USER="aguada"
MQTT_PASS="aguadagtw01"

echo "=== Aguada System Monitor ==="
echo "$(date)"
echo ""

# Check bridge.py running
echo "1. Bridge Status:"
if pgrep -f "bridge.py" > /dev/null; then
    echo "   ✓ bridge.py running (PID $(pgrep -f bridge.py))"
else
    echo "   ✗ bridge.py NOT running"
fi
echo ""

# Check gateway USB
echo "2. Gateway USB:"
if [ -e /dev/ttyACM0 ]; then
    echo "   ✓ /dev/ttyACM0 present"
    lsusb | grep -i espressif | sed 's/^/   /'
else
    echo "   ✗ /dev/ttyACM0 NOT found"
fi
echo ""

# Check MQTT broker
echo "3. MQTT Broker:"
if timeout 2 mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -u $MQTT_USER -P $MQTT_PASS -t "\$SYS/broker/uptime" -C 1 2>&1 | grep -q seconds; then
    echo "   ✓ MQTT broker responding"
else
    echo "   ✗ MQTT broker NOT responding"
fi
echo ""

# Check nodes online
echo "4. Nodes Online:"
timeout 3 mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -u $MQTT_USER -P $MQTT_PASS -t "aguada/+/status" -v 2>&1 | grep online | head -5 | sed 's/^/   /'
echo ""

# Get latest telemetry
echo "5. Latest Telemetry (last 10s):"
timeout 10 mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -u $MQTT_USER -P $MQTT_PASS -t "aguada/+/+/state" -v 2>&1 | while IFS= read -r line; do
    if echo "$line" | grep -q "aguada"; then
        topic=$(echo "$line" | cut -d' ' -f1)
        data=$(echo "$line" | cut -d' ' -f2-)
        alias=$(echo "$data" | jq -r '.alias // "?"')
        level=$(echo "$data" | jq -r '.level_cm // "?"')
        pct=$(echo "$data" | jq -r '.pct // "?"')
        vol=$(echo "$data" | jq -r '.volume_L // "?"')
        echo "   $alias: ${level}cm (${pct}%) ${vol}L"
    fi
done
echo ""

# Check HA Discovery
echo "6. HA Discovery Entities:"
disc_count=$(timeout 2 mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -u $MQTT_USER -P $MQTT_PASS -t "homeassistant/sensor/aguada_+/config" -C 100 2>&1 | wc -l)
echo "   $disc_count Discovery configs published"
echo ""

echo "=== Monitor Complete ==="
