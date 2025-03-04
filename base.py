from enum import Enum, IntEnum, auto, IntFlag

# --- Type Map ---
# Little-endian format is assumed; we use '<' in struct packing calls.
type_map = {
    "enum": "B",
    "uint8_t": "B",
    "uint16_t": "H",
    "uint32_t": "I",
    "uint64_t": "Q",
    "int8_t": "b",
    "int16_t": "h",
    "int32_t": "i",
    "int64_t": "q",
    "float": "f",
    "double": "d",
    "char": "c",
    "bool": "?"
}

# --- Protocol Constants ---
PROTOCOL_VERSION = 1  # Major version; can extend later
MAX_PACKET_SIZE = 220  # Total packet size (bytes)
HEADER_SIZE = 15
SYNC_BYTE = 0xFF  

    
# --- Base Packet Structure Definition ---
base_packet = {
    "header": [
        # Field definitions in order as they will be packed:
        {
            "name": "StartByte", 
            "datatype": "uint8_t", 
            "bitmask": False, 
            "description": "Start Byte"
        },
        {
            "name": "Length", 
            "datatype": "uint8_t", 
            "bitmask": False, 
            "description": "Length of rest of packet (header + payload + checksum)"
        },
        {
            "name": "Version", 
            "datatype": "uint8_t", 
            "bitmask": False, 
            "description": "Protocol version"
        },
        {
            "name": "BinaryFlags", 
            "datatype": "uint8_t", 
            "bitmask": True, 
            "description": "Binary flags"
        },
        {
            "name": "Routing", 
            "datatype": "uint8_t", 
            "bitmask": False, 
            "description": "4-bit TTL, 4-bit reserved flag"
        },
        {
            "name": "RouteSchema", 
            "datatype": "uint8_t",
            "bitmask": False, 
            "description": "Routing Schema"
        },
        {
            "name": "SourceAddr", 
            "datatype": "uint16_t",
            "bitmask": False, 
            "description": "Source Address"
        },
        {
            "name": "DestAddr", 
            "datatype": "uint16_t",
            "bitmask": False, 
            "description": "Destination Address"
        },
        {
            "name": "MessageID", 
            "datatype": "uint16_t", 
            "bitmask": False, 
            "description": "16-bit Message ID (4 bits category, 6 bits type, 6 bits subtype)"
        },
        {
            "name": "Checksum", 
            "datatype": "uint16_t", 
            "bitmask": False, 
            "description": "CRC-16 over header (from flags through payload)"
        }
    ],
    "payload": []
}


"""
Network schemas
N        Words    Bits combo           Address         Nodes      Groups
1        2        [8, 8]               255.255         65025      255       
2        3        [8, 4, 4]            255.15.15       57375      3825      
3        3        [7, 5, 4]            127.31.15       59055      3937      
4        3        [7, 4, 5]            127.15.31       59055      1905      
5        3        [6, 6, 4]            63.63.15        59535      3969      
6        3        [6, 5, 5]            63.31.31        60543      1953      
7        3        [6, 4, 6]            63.15.63        59535      945       
8        3        [5, 7, 4]            31.127.15       59055      3937      
9        3        [5, 6, 5]            31.63.31        60543      1953      
10       3        [5, 5, 6]            31.31.63        60543      961       
11       3        [5, 4, 7]            31.15.127       59055      465       
12       3        [4, 8, 4]            15.255.15       57375      3825      
13       3        [4, 7, 5]            15.127.31       59055      1905      
14       3        [4, 6, 6]            15.63.63        59535      945       
15       3        [4, 5, 7]            15.31.127       59055      465       
16       3        [4, 4, 8]            15.15.255       57375      225       
17       4        [4, 4, 4, 4]         15.15.15.15     50625      3375      
"""
RouteSchemas = [
    [8, 8], 
    [8, 4, 4], 
    [7, 5, 4], 
    [7, 4, 5], 
    [6, 6, 4], 
    [6, 5, 5], 
    [6, 4, 6], 
    [5, 7, 4], 
    [5, 6, 5], 
    [5, 5, 6], 
    [5, 4, 7], 
    [4, 8, 4], 
    [4, 7, 5], 
    [4, 6, 6], 
    [4, 5, 7], 
    [4, 4, 8], 
    [4, 4, 4, 4]
]


# --- Enums and Flags ---

class BinaryFlag(IntFlag):
    # Define individual bit flags for the Binary Flags field (1 byte)
    SIMPLIFIED      = 1 << 0  
    ACK_REQUEST     = 1 << 1  
    REPLY           = 1 << 2  
    ENCRYPTED       = 1 << 3  
    PRIORITY        = 1 << 4
    RESERVED_5      = 1 << 5
    RESERVED_6      = 1 << 6
    RESERVED_7      = 1 << 7

class RoutingFlag(IntFlag):
    # Define individual bit flags for the Binary Flags field (1 byte)
    Q      = 1 << 0  
    W     = 1 << 1  
    E           = 1 << 2  
    R       = 1 << 3  

class MessagePriority(IntEnum):
    FLASH = 0
    IMMEDIATE = auto()
    PRIORITY = auto()
    NORMAL = auto() 
