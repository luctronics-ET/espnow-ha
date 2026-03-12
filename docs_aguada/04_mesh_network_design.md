
# ESP-NOW Mesh Network

Nodes communicate using ESP‑NOW.

## Mesh Features

Neighbor table
RSSI tracking
TTL forwarding
Multi-hop routing

Example topology:

Gateway
  |
 Node1
 /   \
Node2 Node3
       |
     Node4

## Routing Metric

score = RSSI − (hop × 10)

Highest score is chosen as route.
