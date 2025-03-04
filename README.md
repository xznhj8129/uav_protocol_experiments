# uav_protocol_experiments
Experimentation for new autonomy-oriented UAV protocols\
All this is subject to change, very early experimentation\
Code may not work, everything is dirty and jerry-rigged and unoptimized and strewn all over for now

## Overview
The protocol is built for autonomous drone swarming where each node (drone or ground station) communicates over a low-bandwidth link (e.g., LoRa). The packet format includes essential routing information, error checking, and supports a flexible message identifier system that categorizes messages into nested types and flexible network routing with priority to flexible network maps over pure number of unique addresses.

## Key features include:

* Mesh/Swarm Architecture: Explicit support for routing in a multi-hop mesh network.
* Extensibility: A flexible 16-bit MessageID field structured as a nested tree to allow thousands of unique messages.
* Error Tolerance: A CRC-16 checksum ensures data integrity over unreliable links.
* Scalability: Uses a flexible hierarchical addressing and message ID scheme.
* Cursor-on-Target (CoT) Support: Dedicated message category for CoT events to enable rich situational awareness.

## Packet Format
Each packet is composed of a fixed header, an optional payload, and a checksum. The overall packet size is capped at 220 bytes, with a 14-byte header.

## Address Structure

- **Addressing:** 
- <8-bit Network Schema> <16-bit Address>
- Address space: 65,026 unique nodes (1-255)
- The Network Schema byte gives you the opportunity to organize your network in different configurations for better hierarchical organization if necessary.

## Network Schemas
|N | Words | Combination |Addresses | # Nodes | # Groups |
|--|----|--------|---------|-------|-----|
| 1 | 2 | [8, 8] | 255.255 | 65025 | 255 |
| 2 | 3 | [8, 4, 4] | 255.15.15 | 57375 | 3825 |
| 3 | 3 | [7, 5, 4] | 127.31.15 | 59055 | 3937 |
| 4 | 3 | [7, 4, 5] | 127.15.31 | 59055 | 1905 |
| 5 | 3 | [6, 6, 4] | 63.63.15 | 59535 | 3969 |
| 6 | 3 | [6, 5, 5] | 63.31.31 | 60543 | 1953 |
| 7 | 3 | [6, 4, 6] | 63.15.63 | 59535 | 945 |
| 8 | 3 | [5, 7, 4] | 31.127.15 | 59055 | 3937 |
| 9 | 3 | [5, 6, 5] | 31.63.31 | 60543 | 1953 |
| 10 | 3 | [5, 5, 6] | 31.31.63 | 60543 | 961 |
| 11 | 3 | [5, 4, 7] | 31.15.127 | 59055 | 465 |
| 12 | 3 | [4, 8, 4] | 15.255.15 | 57375 | 3825 |
| 13 | 3 | [4, 7, 5] | 15.127.31 | 59055 | 1905 |
| 14 | 3 | [4, 6, 6] | 15.63.63 | 59535 | 945 |
| 15 | 3 | [4, 5, 7] | 15.31.127 | 59055 | 465 |
| 16 | 3 | [4, 4, 8] | 15.15.255 | 57375 | 225 |
| 17 | 4 | [4, 4, 4, 4] | 15.15.15.15 | 50625 | 3375 |

### Field Breakdown

| Field                   | Size (bytes) | Description                                                                                                  |
|-------------------------|--------------|--------------------------------------------------------------------------------------------------------------|
| **Start Byte**          | 1            | Fixed start marker for frame synchronization.                                |
| **Length**              | 1            | Length of the remainder of the packet (header body + payload + checksum).                                     |
| **Version**             | 1            | Protocol version (allows for future backward-compatible changes).                                             |
| **Binary Flags**        | 1            | Bitmask for control flags such as ACK request, reply, encryption, and priority.                               |
| **TTL / Routing**       | 1            | Contains a 4-bit Time-To-Live (TTL) for limiting hops and 4 reserved bits for future use.                      |
| **Network Schema**      | 1            | Hierarchical Network Schema
| **Source Address**      | 2            | Hierarchical source address
| **Destination Address** | 2            | Hierarchical destination address
| **MessageID**           | 2            | 16-bit Message Identifier split into 4 bits (category), 6 bits (message type), and 6 bits (subtype).            |
| **Checksum**            | 2            | CRC-16 computed over the header (starting at Binary Flags) and payload to ensure integrity.                   |
| **Payload**             | 0–205        | Variable-length data (up to 205 bytes) defined by the message type.                                           |

*Total header overhead: 14 bytes. Maximum payload: 205 bytes.*


## MessageID Structure

The **MessageID** is a 16-bit field that is subdivided to provide a clear and extensible categorization:

- **4 bits:** Primary Category (0–15)
- **6 bits:** Message Type (0–63)
- **6 bits:** Message Subtype (0–63)

This allows for a total of 16 × 64 × 64 = **65,536 distinct message identifiers**.

### Nested MessageID Tree

Instead of a flat list, message identifiers are organized in a nested tree structure:

- **Telemetry:**  
  - `MessageID.Telemetry.POSITION`  
  - `MessageID.Telemetry.BATTERY`  
  - `MessageID.Telemetry.ATTITUDE`
- **Command:**  
  - `MessageID.Command.SET_MISSION`  
  - `MessageID.Command.SET_POSITION`  
  - `MessageID.Command.PHASE`
- **Routing:**  
  - `MessageID.Routing.HEARTBEAT`  
  - `MessageID.Routing.STATUS`

The `encode_message_id` function packs these components into a single 16-bit integer, and the `decode_message_id` function decodes it back into a tuple `(category, message type, subtype)`.

---

## Packet Packing & Unpacking

The protocol provides two utility functions:

- **`pack_packet()`**  
  Constructs a packet from the provided fields:
  - **Parameters:**  
    - `flags` (BinaryFlag): Control flags (e.g., ACK_REQUEST).  
    - `routing` (uint8_t): Time-To-Live value
    - `network_schema` (uint8_t): Network schema index
    - `source` (uint16_t): Source node address.  
    - `destination` (uint16_t): Destination node address.  
    - `message_id` (uint8_t): Encoded 16-bit MessageID.  
    - `payload` (bytes): The variable-length payload.
  - **Returns:** A complete byte string representing the packet.

- **`unpack_packet()`**  
  Parses a received packet and validates its integrity using the CRC-16 checksum.
  - **Returns:** A dictionary containing all header fields and the raw payload

---

## CRC-16 Checksum

A CRC-16/CCITT checksum (using polynomial `0x1021` with the `crcmod` library) is computed over all header fields from the Binary Flags to the end of the payload. This mechanism detects any corruption in the transmitted packet.

---

## Example Usage (wip, obviously)

* Look at message_definitions.csv and base.py to define messages
* python3 definitions.py
* python3 test_protocol.py (see in there for usage, sketchy for now)