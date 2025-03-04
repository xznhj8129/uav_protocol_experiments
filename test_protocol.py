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

def encode_address(segments: tuple, schema: list) -> int:
    """
    Encode a tuple of address segments into a 16-bit integer,
    according to the provided schema (a list of bit lengths that sum to 16).
    """
    if len(segments) != len(schema):
        raise ValueError("Number of segments does not match the schema length.")
    if sum(schema) != 16:
        raise ValueError("Schema must sum to 16 bits.")
    
    result = 0
    shift = 16
    for seg, bits in zip(segments, schema):
        shift -= bits
        if seg >= (1 << bits):
            raise ValueError(f"Segment value {seg} too high for allocated {bits} bits.")
        result |= (seg & ((1 << bits) - 1)) << shift
    return result

def decode_address(addr_int: int, schema: list) -> tuple:
    """
    Decode a 16-bit integer into a tuple of address segments
    based on the provided schema (list of bit lengths that sum to 16).
    """
    if sum(schema) != 16:
        raise ValueError("Schema must sum to 16 bits.")
    
    segments = []
    shift = 16
    for bits in schema:
        shift -= bits
        seg = (addr_int >> shift) & ((1 << bits) - 1)
        segments.append(seg)
    return tuple(segments)

class Address:
    """
    Represents a 16-bit address with a given routing schema.
    The address is split into segments as defined by the schema.
    
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
        Convert the address segments into a 16-bit integer based on the chosen schema.
        """
        schema = RouteSchemas[self.schema_index]
        return encode_address(self.segments, schema)

    def to_bytes(self) -> bytes:
        """
        Return the 16-bit encoded address as 2 bytes (little-endian).
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

    def __str__(self):
        """
        Return the address as a dot-separated string of segments.
        """
        return ".".join(str(seg) for seg in self.segments)



# --- Helper Functions for MessageID ---

def encode_message_id(category: int, msg_type: int, subtype: int) -> int:
    """
    Encode a 16-bit MessageID from:
      - category: 4 bits (0-15)
      - msg_type: 6 bits (0-63)
      - subtype: 6 bits (0-63)
    """
    print('ENCODE ID:', category, msg_type, subtype)
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
    print('DECODE ID:', category, msg_type, subtype)
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


def pack_packet(flags: BinaryFlag, ttl: int, route_schema: int,
                source: Address, destination: Address, message_id: int,
                payload: bytes) -> bytes:
    """
    Pack the packet dynamically based on the base_packet header definition.
    This function computes offsets using the type map so nothing is hardcoded.
    
    Parameters:
      - flags: BinaryFlag value (1 byte).
      - ttl: Routing TTL (1 byte).
      - route_schema: Routing schema value (uint16_t).
      - source: Source Address (Address object).
      - destination: Destination Address (Address object).
      - message_id: 16-bit MessageID.
      - payload: Payload bytes.
      
    Returns:
      A complete packet as a bytes object.
    """

    # yikes my dude
    qwe = messageid(message_id)
    rty = encode_message_id(*qwe)

    # Build header values dictionary.
    header_values = {
        "StartByte": SYNC_BYTE,
        "Length": 0,  # Placeholder; computed below.
        "Version": PROTOCOL_VERSION,
        "BinaryFlags": flags.value,
        "Routing": ttl & 0xFF,
        "RouteSchema": route_schema & 0xFFFF,
        "SourceAddr": source.to_int() & 0xFFFF,
        "DestAddr": destination.to_int() & 0xFFFF,
        "MessageID": rty & 0xFFFF,
        # "Checksum": to be computed.
    }
    
    # Split header into three parts: fixed fields, body, and checksum.
    fixed_fields = base_packet['header'][:3]         # StartByte, Length, Version
    body_fields = base_packet['header'][3:-1]          # BinaryFlags, Routing, RouteSchema, SourceAddr, DestAddr, MessageID
    checksum_field = base_packet['header'][-1]         # Checksum
    
    fixed_fmt = "<" + "".join(type_map[field["datatype"]] for field in fixed_fields)
    body_fmt  = "<" + "".join(type_map[field["datatype"]] for field in body_fields)
    checksum_fmt = "<" + type_map[checksum_field["datatype"]]
    
    fixed_size = struct.calcsize(fixed_fmt)
    body_size  = struct.calcsize(body_fmt)
    checksum_size = struct.calcsize(checksum_fmt)  # Typically 2 bytes.
    
    # Compute total length for fields after the fixed header:
    total_length = body_size + len(payload) + checksum_size
    # Update the Length field.
    header_values["Length"] = total_length
    
    # Pack fixed header.
    fixed_values = [header_values[field["name"]] for field in fixed_fields]
    fixed_header = struct.pack(fixed_fmt, *fixed_values)
    
    # Pack body fields.
    body_values = [header_values[field["name"]] for field in body_fields]
    header_body = struct.pack(body_fmt, *body_values)
    
    # Compute CRC over header body (from BinaryFlags through MessageID) and payload.
    crc_data = header_body + payload
    checksum = crc16(crc_data)
    checksum_bytes = struct.pack(checksum_fmt, checksum)
    
    # Assemble final packet.
    packet = fixed_header + header_body + payload + checksum_bytes
    
    if len(packet) > MAX_PACKET_SIZE:
        raise ValueError("Packet exceeds maximum allowed size.")
    
    return packet

def unpack_packet(packet: bytes, schema_index: int = 1) -> dict:
    """
    Unpack a packet dynamically based on the base_packet header definition.
    Returns a dictionary with header fields and payload.
    The MessageID is decoded into a tuple (category, type, subtype).
    """
    if len(packet) < struct.calcsize("<" + "".join(type_map[field["datatype"]] for field in base_packet['header'])):
        raise ValueError("Packet too short.")
    
    fixed_fields = base_packet['header'][:3]         # StartByte, Length, Version
    body_fields = base_packet['header'][3:-1]          # BinaryFlags, Routing, RouteSchema, SourceAddr, DestAddr, MessageID
    checksum_field = base_packet['header'][-1]         # Checksum
    
    fixed_fmt = "<" + "".join(type_map[field["datatype"]] for field in fixed_fields)
    body_fmt  = "<" + "".join(type_map[field["datatype"]] for field in body_fields)
    checksum_fmt = "<" + type_map[checksum_field["datatype"]]
    
    fixed_size = struct.calcsize(fixed_fmt)
    body_size  = struct.calcsize(body_fmt)
    checksum_size = struct.calcsize(checksum_fmt)
    
    # Unpack fixed header.
    fixed_values = struct.unpack(fixed_fmt, packet[:fixed_size])
    header_values = {}
    for field, value in zip(fixed_fields, fixed_values):
        header_values[field["name"]] = value
    
    total_length = header_values["Length"]
    expected_total = fixed_size + total_length
    if len(packet) != expected_total:
        raise ValueError("Packet length mismatch.")
    
    offset = fixed_size
    # Unpack body fields.
    body_values = struct.unpack(body_fmt, packet[offset:offset+body_size])
    for field, value in zip(body_fields, body_values):
        header_values[field["name"]] = value
    offset += body_size
    
    # Extract payload.
    payload = packet[offset:-checksum_size]
    offset = len(packet) - checksum_size
    (recv_checksum,) = struct.unpack(checksum_fmt, packet[offset:])
    
    # Compute and validate CRC over body fields and payload.
    crc_data = packet[fixed_size: fixed_size+body_size] + payload
    calc_checksum = crc16(crc_data)
    if calc_checksum != recv_checksum:
        raise ValueError("Checksum mismatch.")

    src_bytes = struct.pack('<H', header_values["SourceAddr"])
    src_addr_obj = Address.from_bytes(src_bytes, schema_index)
    header_values["SourceAddr"] = str(src_addr_obj)

    dst_bytes = struct.pack('<H', header_values["DestAddr"])
    dst_addr_obj = Address.from_bytes(dst_bytes, schema_index)
    header_values["DestAddr"] = str(dst_addr_obj)
    
    # Decode MessageID into a tuple (category, type, subtype).
    header_values["MessageID"] = decode_message_id(header_values["MessageID"])
    
    # Append payload and checksum.
    header_values["Payload"] = payload
    header_values["Checksum"] = recv_checksum
    
    return header_values

# --- Example Usage ---
if __name__ == "__main__":
    # Define example addresses with a chosen schema.
    # For instance, using schema index 1 ([8, 4, 4]): Group (8 bits), Subgroup (4 bits), Node (4 bits)
    schema_index = 1
    src_addr = Address((200, 10, 5), schema_index)
    dst_addr = Address((100, 7, 12), schema_index)
    
    # Example payload.
    payload = b""
    
    # Example parameters.
    flags = BinaryFlag.ACK_REQUEST
    ttl = 15

    # Pack the packet.
    print(messageid(Messages.Command.Mission.SET_MISSION))

    packet = pack_packet(
        BinaryFlag.ACK_REQUEST, 
        ttl,
        schema_index, 
        src_addr, 
        dst_addr,
        Messages.Command.Mission.SET_MISSION, 
        payload
        )
    print("Packed Packet (hex):", packet.hex())
    print(len(packet))
    
    # Unpack the packet, specifying the schema index for address decoding.
    unpacked = unpack_packet(packet, schema_index=schema_index)
    print("Unpacked Packet:", unpacked)
    
    # Pack a packet using a Cursor-on-Target event.
    # Using the nested MessageID: MessageID.CotEvent.GENERIC
    print("Packed Packet (hex):", packet.hex())
    
    # Unpack the packet.
    unpacked = unpack_packet(packet)
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