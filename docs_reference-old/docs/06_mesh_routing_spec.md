# ESP-NOW Mesh Routing Specification

## Objective

Provide a lightweight multi-hop routing mechanism suitable for low-power
ESP32 sensor networks.

The design favors: - simplicity - robustness - low memory usage

## Neighbor Discovery

Each node periodically sends:

HELLO packet

Contents: node_id hop_to_gateway battery rssi

Neighbors store this information in a table.

## Neighbor Table Structure

node_id RSSI hop_to_gateway last_seen

Example:

  Node   RSSI   Hop
  ------ ------ -----
  N1     -62    1
  N3     -70    2

## Route Selection

Score calculation:

score = RSSI - (hop \* 10)

Highest score is chosen.

## Packet Forwarding

Rules:

1.  If destination == node → process
2.  If TTL \> 0 → forward
3.  If packet already seen → ignore

TTL prevents infinite loops.

## Packet Cache

Each node stores recent packet IDs:

src + seq

Size example:

16 entries

## Network Healing

If a neighbor disappears:

-   remove entry
-   recompute route

Mesh automatically adapts.
