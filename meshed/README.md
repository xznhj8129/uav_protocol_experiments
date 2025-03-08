# Flexible mesh network communication library
Uses defined protocol and msgpack to send data over flexible links\
Significantly simplified and integrated with my other libraries\
Cursor-on-Target support\

**Transport layers support:**
- Meshtastic
- UDP
- ???

## Requirements:
- [FrogCoT](https://github.com/xznhj8129/frogcot)
- [FrogGeoLib](https://github.com/xznhj8129/froggeolib)
- [FrogTastic](https://github.com/xznhj8129/frogtastic)

## Usage:
- Define messages in message_definitions.csv (for now)
- run definitions.py, generates .json and enums file (soon start from json alone)
- payload_enums.py defines enums of packed binary enum values
- protocol.py defines usage and structure
- datalinks.py defines transport interface
- nodes.json is your network map

## Test:
- right now just uses an INAV MSP flight controller, mavlink soon for primary focus