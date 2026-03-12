
# Mesh Algorithm

Each node maintains a neighbor table.

Fields:
node_id
RSSI
hop_to_gateway
last_seen

Route selection score:

score = RSSI - (hop * 10)

Forwarding rule:

if dst == self -> process
else if ttl > 0 -> forward
