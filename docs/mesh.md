
# Mesh Routing

Each node maintains:

Neighbor table
Route score
Packet cache

Route score:

score = RSSI - (hop * 10)

Routing decision:

if destination == node:
    process
else:
    forward with ttl--
