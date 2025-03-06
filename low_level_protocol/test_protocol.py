from enum import Enum, IntEnum, auto, IntFlag
from base import *
import struct
import crcmod
import time
from typing import Any, Dict, List
from enum import Enum, IntEnum, auto
from typing import List, Dict, Tuple, Optional, Any
from base import *
from definitions import MessageDefinitions
from message_structure import *
from payload_enums import *



# --- Helper Functions for MessageID ---

def encode_message_id(category: int, msg_type: int, subtype: int) -> int:
    """
    Encode a 16-bit MessageID from:
      - category: 4 bits (0-15)
      - msg_type: 6 bits (0-63)
      - subtype: 6 bits (0-63)
    """
    if not (0 <= category < 16):
        raise ValueError("Category must be in range 0-15")
    if not (0 <= msg_type < 64):
        raise ValueError("Message type must be in range 0-63")
    if not (0 <= subtype < 64):
        raise ValueError("Subtype must be in range 0-63")
    return (category << 12) | (msg_type << 6) | subtype

def decode_message_id(message_id: int):
    """
    Decode a 16-bit MessageID into a tuple (category, msg_type, subtype).
    """
    category = (message_id >> 12) & 0xF
    msg_type = (message_id >> 6) & 0x3F
    subtype = message_id & 0x3F
    return category, msg_type, subtype

# --- CRC Functionality ---
# Using CRC-16/CCITT (polynomial 0x1021) for our checksum.
crc16 = crcmod.predefined.mkCrcFun('crc-ccitt-false')

def messageid(msg):
    # Get the enum class (e.g., Messages.Command.Mission)
    enum_class = msg.__class__
    # Get the qualified name (e.g., 'Messages.Command.Mission')
    qualname = enum_class.__qualname__
    # Split into parts: ['Messages', 'Command', 'Mission']
    parts = qualname.split('.')
    # Ensure it's the expected structure
    if len(parts) != 3 or parts[0] != 'Messages':
        raise ValueError("Invalid message enum")
    category_name = parts[1]  # e.g., 'Command'
    subcategory_name = parts[2]  # e.g., 'Mission'
    
    # Get category value from MessageCategory
    category_enum = getattr(MessageCategory, category_name)
    category_value = category_enum.value
    
    # Get subcategory value from Messages.Category.Subcategory.value
    category_class = getattr(Messages, category_name)
    subcategory_class = getattr(category_class, subcategory_name)
    subcategory_value = subcategory_class.value
    
    # Get message value from the enum member itself
    message_value = msg.value
    
    return (category_value, subcategory_value, message_value)

# ---------------------------------------------------------------------------
# Packet Encoder/Decoder Implementation (Dynamically Loaded)
# ---------------------------------------------------------------------------

def get_header_format() -> str:
    fmt = ""
    for field in base_packet["header"]:
        fmt += type_map[field["datatype"]]
    return fmt

def get_payload_format(payload_defs: List[Dict[str, Any]]) -> str:
    fmt = ""
    for field in payload_defs:
        fmt += type_map[field["datatype"]]
    return fmt


# ---------------------------------------------------------------------------
# Address Encoder/Decoder
# ---------------------------------------------------------------------------

def encode_address(segments: tuple, schema: list) -> int:
    """
    Encode a tuple of address segments into an integer,
    according to the provided schema (a list of bit lengths that sum to 16/20).
    """
    if len(segments) != len(schema):
        raise ValueError("Number of segments does not match the schema length.")
    if (len(schema) > 1 and sum(schema) != 16) or (len(schema) == 1 and sum(schema) != 20):
        raise ValueError("Address space overflow")
    
    result = 0
    shift = 20 if len(schema) == 1 else 16 
    for seg, bits in zip(segments, schema):
        shift -= bits
        if seg >= (1 << bits):
            raise ValueError(f"Segment value {seg} too high for allocated {bits} bits.")
        result |= (seg & ((1 << bits) - 1)) << shift
    return result

def decode_address(addr_int: int, schema: list) -> tuple:
    """
    Decode a integer into a tuple of address segments
    based on the provided schema (list of bit lengths that sum to 16).
    """
    if (len(schema) > 1 and sum(schema) != 16) or (len(schema) == 1 and sum(schema) != 20):
        raise ValueError("Address space overflow")
    
    segments = []
    shift = 20 if len(schema) == 1 else 16 
    for bits in schema:
        shift -= bits
        seg = (addr_int >> shift) & ((1 << bits) - 1)
        segments.append(seg)
    return tuple(segments)

class Address:
    """
    Represents an address with a given routing schema.
    The address is split into segments as defined by the schema.
    
    If not using schemas, address is 20 bits.
    If using schemas, address is 16 bits.

    For example, using schema [8, 4, 4]:
      - The address is composed of three segments: (A, B, C)
      - 'A' is 8 bits (0-255), 'B' is 4 bits (0-15), 'C' is 4 bits (0-15)
      - The complete 16-bit address is encoded as: (A << 8) | (B << 4) | C
    """
    def __init__(self, segments: tuple, schema_index: int):
        if schema_index < 0 or schema_index >= len(RouteSchemas):
            raise ValueError("Invalid schema index.")
        self.schema_index = schema_index
        schema = RouteSchemas[schema_index]
        if len(segments) != len(schema):
            raise ValueError("Segments length does not match the schema.")
        for seg, bits in zip(segments, schema):
            if seg >= (1 << bits):
                raise ValueError(f"Segment value {seg} exceeds {bits} bits limit.")
        self.segments = segments

    def to_int(self) -> int:
        """
        Convert the address segments into an integer based on the chosen schema.
        """
        schema = RouteSchemas[self.schema_index]
        return encode_address(self.segments, schema)

    def to_bytes(self) -> bytes:
        """
        Return the encoded address as 2 bytes (little-endian).
        """
        addr_int = self.to_int()
        return struct.pack('<H', addr_int)

    @classmethod
    def from_bytes(cls, data: bytes, schema_index: int):
        """
        Create an Address object from 2 bytes of data and a specified schema index.
        """
        if len(data) < 2:
            raise ValueError("Not enough data to extract address.")
        (addr_int,) = struct.unpack('<H', data[:2])
        schema = RouteSchemas[schema_index]
        segments = decode_address(addr_int, schema)
        return cls(segments, schema_index)

    @classmethod
    def from_int(cls, addr_int: int, schema_index: int):
        """
        Create an Address object from an integer and schema index.

        Parameters:
            - addr_int: Integer representation of the address (16-bit or 20-bit).
            - schema_index: Index into RouteSchemas.

        Returns:
            An Address object.
        """
        schema = RouteSchemas[schema_index]
        segments = decode_address(addr_int, schema)  # Assume decode_address exists
        return cls(segments, schema_index)

    def __str__(self):
        """
        Return the address as a dot-separated string of segments.
        """
        if len(self.segments)==1:
            return str(self.segments[0])
        else:
            return ".".join(str(seg) for seg in self.segments)



# fragment
class Packet:
    def __init__(self, data: Dict[str, Any]):
        # Recursively set attributes from the decoded data
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Packet(value))
            else:
                setattr(self, key, value)
        self._data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Return the original decoded packet as a dictionary.
        """
        return self._data

    def __repr__(self):
        return f"Packet({self._data})"

def encode_packet(flags: BinaryFlag, routing: RoutingFlag, route_schema: int,
                sender: list, receiver: list, message_id: int,
                payload: bytes) -> bytes:
    """
    Pack the packet dynamically based on routing flags.

    Parameters:
        - flags: BinaryFlag value (1 byte).
        - routing: RoutingFlag with TTL in upper 4 bits and flags in lower 4 bits (1 byte).
        - route_schema: 8-bit Schema index space (used if ROUTE_SCHEMA flag is set).
        - source: 16-bit Address space.
        - destination: 16-bit Address space.
        - message_id: 16-bit MessageID.
        - payload: Payload bytes.

    Returns:
        A complete packet as a bytes object.
    """
    # Encode MessageID
    qwe = messageid(message_id)
    encoded_message_id = encode_message_id(*qwe)

    source = Address(sender, schema_index)
    destination = Address(receiver, schema_index)

    # Fixed header: StartByte, Length (placeholder), Version
    fixed_header = struct.pack("<BBB", SYNC_BYTE, 0, PROTOCOL_VERSION)

    # Common body fields
    binary_flags_bytes = struct.pack("<B", flags.value)
    # Assume routing.value includes TTL (bits 7-4) and flags (bits 3-0)
    routing_byte = struct.pack("<B", routing.value)

    # Dynamic address fields based on ROUTE_SCHEMA flag
    if routing & RoutingFlag.ROUTE_SCHEMA:
        route_schema_byte = struct.pack("<B", route_schema)
        source_addr_bytes = struct.pack("<H", source.to_int() & 0xFFFF)
        dest_addr_bytes = struct.pack("<H", destination.to_int() & 0xFFFF)
        addresses_part = route_schema_byte + source_addr_bytes + dest_addr_bytes
    else:
        # Pack two 20-bit addresses into 5 bytes
        source_int = source.to_int() & 0xFFFFF  # Ensure 20-bit max
        dest_int = destination.to_int() & 0xFFFFF  # Ensure 20-bit max
        combined = (source_int << 20) | dest_int  # 40 bits
        addresses_part = combined.to_bytes(5, 'little')

    # MessageID
    message_id_bytes = struct.pack("<H", encoded_message_id & 0xFFFF)

    # Assemble data for checksum: BinaryFlags through payload
    crc_data = binary_flags_bytes + routing_byte + addresses_part + message_id_bytes + payload
    checksum = crc16(crc_data)
    checksum_bytes = struct.pack("<H", checksum)

    # Total packet
    packet = fixed_header + crc_data + checksum_bytes

    # Update Length: size of everything after fixed header
    length = len(packet) - 3  # Exclude StartByte, Length, Version
    packet = struct.pack("<BBB", SYNC_BYTE, length, PROTOCOL_VERSION) + packet[3:]

    if len(packet) > MAX_PACKET_SIZE:
        raise ValueError("Packet exceeds maximum allowed size.")

    return packet

def decode_packet(packet: bytes) -> dict:
    """
    Unpack a packet dynamically based on routing flags.

    Parameters:
        - packet: Bytes object containing the packet.

    Returns:
        A dictionary with header fields, parsed flags, addresses, and payload.
        MessageID is decoded into (category, type, subtype).
    """
    if len(packet) < 6:  # Minimum: StartByte, Length, Version, BinaryFlags, Routing, Checksum
        raise ValueError("Packet too short.")

    # Unpack fixed header
    start_byte, length, version = struct.unpack("<BBB", packet[:3])
    if start_byte != SYNC_BYTE:
        raise ValueError("Invalid start byte.")
    if version != PROTOCOL_VERSION:
        raise ValueError("Unsupported protocol version.")

    offset = 3
    binary_flags = struct.unpack("<B", packet[offset:offset+1])[0]
    offset += 1
    routing_byte = struct.unpack("<B", packet[offset:offset+1])[0]
    offset += 1

    # Parse Routing byte
    ttl = (routing_byte >> 4) & 0xF
    routing_flags = RoutingFlag(routing_byte & 0xF)

    # Dynamic address parsing
    if routing_flags & RoutingFlag.ROUTE_SCHEMA:
        route_schema = struct.unpack("<B", packet[offset:offset+1])[0]
        offset += 1
        source_int = struct.unpack("<H", packet[offset:offset+2])[0]
        offset += 2
        dest_int = struct.unpack("<H", packet[offset:offset+2])[0]
        offset += 2
        schema_index = route_schema
    else:
        combined = int.from_bytes(packet[offset:offset+5], 'little')
        source_int = combined >> 20
        dest_int = combined & 0xFFFFF  # 20-bit mask
        offset += 5
        schema_index = 0  # No schema, 20-bit addresses

    # MessageID
    message_id = struct.unpack("<H", packet[offset:offset+2])[0]
    offset += 2

    # Payload and checksum
    payload_end = len(packet) - 2  # Exclude checksum
    payload = packet[offset:payload_end]
    checksum_received = struct.unpack("<H", packet[payload_end:])[0]

    # Verify length
    expected_length = offset + len(payload) + 2 - 3  # From BinaryFlags to end
    if length != expected_length:
        raise ValueError("Packet length mismatch.")

    # Verify checksum
    crc_data = packet[3:payload_end]  # BinaryFlags through payload
    calc_checksum = crc16(crc_data)
    if calc_checksum != checksum_received:
        raise ValueError("Checksum mismatch.")

    # Create Address objects
    source_addr = Address.from_int(source_int, schema_index)
    dest_addr = Address.from_int(dest_int, schema_index)

    # Return parsed fields
    return {
        "StartByte": start_byte,
        "Length": length,
        "Version": version,
        "BinaryFlags": BinaryFlag(binary_flags),
        "Routing": routing_byte,
        "TTL": ttl,
        "RoutingFlags": routing_flags,
        "RouteSchema": route_schema if routing_flags & RoutingFlag.ROUTE_SCHEMA else None,
        "SourceAddr": str(source_addr),
        "DestAddr": str(dest_addr),
        "MessageID": decode_message_id(message_id),
        "Payload": payload,
        "Checksum": checksum_received,
    }

# --- Example Usage ---
if __name__ == "__main__":
    # Define example addresses with a chosen schema.
    schema_index = 1
    src_addr = [0,0]
    dst_addr = [255,255]
    print("Sender:", src_addr)
    print('Destination:', dst_addr)
    
    # Example payload.
    payload = b""
    
    # Example parameters.
    msgflags = BinaryFlag.ACK_REQUEST
    routingflags = RoutingFlag(0)

    # Pack the packet.
    print(messageid(Messages.Command.Mission.SET_MISSION))

    packet = encode_packet(
        msgflags, 
        routingflags,
        schema_index, 
        src_addr, 
        dst_addr,
        Messages.Command.Mission.SET_MISSION, 
        payload
        )
    print("Packed Packet (hex):", packet.hex())
    print(len(packet))
    
    # Unpack the packet, specifying the schema index for address decoding.
    unpacked = decode_packet(packet)
    print("Unpacked Packet:", unpacked)
    
    # Pack a packet using a Cursor-on-Target event.
    # Using the nested MessageID: MessageID.CotEvent.GENERIC
    print("Packed Packet (hex):", packet.hex())
    
    # Unpack the packet.
    unpacked = decode_packet(packet)
    print("Unpacked Packet:", unpacked)

    print('-',MessageCategory.Command)
    # Expected output: 1  (its enum integer value)

    print('-',Messages.System.Status)
    # Expected output: 1  (its enum integer value)

    print('-',Messages.System.Status.HEARTBEAT)
    # Expected output: 1  (its enum integer value)

    print('-',Messages.Command.Mission.SET_MISSION.payload)
    # Expected output:
    # [{'name': 'lattitude', 'datatype': 'int32_t', 'bitmask': False}, {'name': 'longitude', 'datatype': 'int32_t', 'bitmask': False}]

    exit()
    ####################################################################################
    print('#' * 32)
    print("!!! OLD CODE!!! ")
    print('#' * 32)

    print('-',MessageCategory.Command)
    # Expected output: 1  (its enum integer value)

    print('-',MessageType.System)
    # Expected output: 0  (its enum integer value)
    
    print('-',Messages.Status.System.FLIGHT.payload)
    # Expected output:
    # [{'name': 'FlightMode', 'datatype': 'enum', 'bitmask': False},
    #  {'name': 'airspeed', 'datatype': 'uint8_t', 'bitmask': False},
    #  {'name': 'groundspeed', 'datatype': 'uint8_t', 'bitmask': False},
    #  {'name': 'heading', 'datatype': 'uint8_t', 'bitmask': False},
    #  {'name': 'msl_alt', 'datatype': 'uint16_t', 'bitmask': False}]

    print('-',Messages.Status.System.FLIGHT)
    # Expected output: 1  (its enum integer value)

    print('-',PayloadEnum.Event_Mission_Phase.ONLINE)
    print('-',PayloadEnum.CommandResult.ACCEPTED)
    # Expected output: 1  (its enum integer value)

    print("\n --- Packet ---")
    packet = Messages.Event.Mission.PHASE.encode(
        to_team=1,
        from_team=1,
        from_id=0,
        to_id=255,
        timestamp=int(time.time()),
        priority=MessagePriority.Normal,
        error=False,
        ent_type=EntityType.Unit,
        payload_Event_Mission_Phase=PayloadEnum.Event_Mission_Phase.ONLINE,  
    )

    print('-',packet)  # prints the packed bytes object
    decoded = decode_packet(packet)
    print('-',decoded)
    print('-','category',MessageCategory(decoded.category).name)
    print('-','type',decoded.system_or_mission, MessageType(decoded.system_or_mission).name)
    print('-','subtype',Messages.Event.Mission(decoded.subtype).name)
    print('-',EntityType(decoded.ent_type).name)
    print('-',decoded.payload)
    print('-','Event_Mission_Phase',PayloadEnum.Event_Mission_Phase(decoded.payload.Event_Mission_Phase).name)

    # Heartbeat test
    print("\n --- Heartbeat ---")
    hb = Messages.Heartbeat.encode(
        to_team=1,
        from_team=1,
        from_id=0,
        to_id=255,
        timestamp=int(time.time()),
        ent_type=EntityType.Unit
    )
    print('-',hb)
    decoded = decode_packet(hb)
    print('-',decoded)
    print('-',decoded.timestamp)

    # Reply test
    print("\n --- Command Reply ---")
    packet = Messages.Command.Mission.SET_MISSION.encode(
        reply=True,
        to_team=1,
        from_team=1,
        from_id=0,
        to_id=255,
        timestamp=int(time.time()),
        priority=MessagePriority.Normal,
        error=False,
        ent_type=EntityType.Unit,
        payload_CommandResult=PayloadEnum.CommandResult.IN_PROGRESS,  
    )

    print('-',packet)  # prints the packed bytes object
    decoded = decode_packet(packet)
    print('-',decoded)
    print('-','category',MessageCategory(decoded.category).name)
    print('-','type',decoded.system_or_mission, MessageType(decoded.system_or_mission).name)
    print('-','subtype',Messages.Command.Mission(decoded.subtype).name)
    print('-', "is reply" if decoded.reply else "not reply")
    if decoded.reply:
        print('-','CommandResult',PayloadEnum.CommandResult(decoded.payload.CommandResult).name)

    # Data error test
    print("\n --- Data Error ---")
    packet = Messages.Data.Mission.QUERY_MISSION_ID.encode(
        reply=True,
        to_team=1,
        from_team=1,
        from_id=0,
        to_id=255,
        timestamp=int(time.time()),
        priority=MessagePriority.Normal,
        error=True,
        ent_type=EntityType.Unit,
        payload_DataError=PayloadEnum.DataError.NOT_FOUND,  
    )

    print('-',packet)  # prints the packed bytes object
    decoded = decode_packet(packet)
    print('-',decoded)
    print('-','category',MessageCategory(decoded.category).name)
    print('-','type',decoded.system_or_mission, MessageType(decoded.system_or_mission).name)
    print('-','subtype',Messages.Data.Mission(decoded.subtype).name)
    print('-', "is reply" if decoded.reply else "not reply")
    if decoded.reply:
        print('-','DataError',PayloadEnum.DataError(decoded.payload.DataError).name)