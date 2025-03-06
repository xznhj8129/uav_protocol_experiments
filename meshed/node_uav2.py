#!/usr/bin/env python3

import asyncio
import msgpack
import socket
from unavlib.control import UAVControl
from unavlib.modules import geospatial
from unavlib.modules.utils import inavutil
from frogtastic import MeshtasticClient
import froggeolib
import frogcot
from message_structure import Messages
from transport import Transport
from protocol import *


# Constants
RADIO_PORT = '/dev/ttyUSB0'
LINK_PORT = 260  # Meshtastic port
TELEMETRY_PORT = '/dev/ttyACM1'
MY_ID = "drone1"
SEND_INTERVAL = 5
PRELOAD_MODES = [27, 10, 12, 38]
SOCKET_HOST = '127.0.0.1'  # Localhost for testing
SOCKET_PORT = 5555

# Transport configuration
USE_MESHTASTIC = True 
USE_SOCKET = False

modemap = [27, 10, 12, 38, 0, 1, 53, 11, 31, 47]

nodemap = {
    "gcs1": {
        "meshid": "!55c7628c",
        "ip": "127.0.0.1:5556",
        "routes": {}
    },
    "drone1": {
        "meshid": "!3364355c",
        "ip": "127.0.0.1:5555",
        "routes": {}
    },
}


def list_to_int(indices):
    bitmap = 0
    for i in indices:
        bitmap |= (1 << i)
    return bitmap

async def main():
    # Initialize transports
    mesh_client = MeshtasticClient(RADIO_PORT) if USE_MESHTASTIC else None
    sock = None
    if USE_SOCKET:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)  # Non-blocking for asyncio
        sock.bind(('', SOCKET_PORT))  # UAV listens on this port

    transport = Transport(mesh_client=mesh_client, sock=sock)
    transport.nodemap = nodemap
    uav_id = mesh_client.meshint.getMyNodeInfo()["user"]["id"] if mesh_client else "UAV_SOCKET"
    print(f"[INIT] My node ID: {uav_id}")

    # Initialize UAV
    mydrone = UAVControl(device=TELEMETRY_PORT, baudrate=115200, platform="AIRPLANE")
    mydrone.msp_receiver = False
    mini_modes = PRELOAD_MODES.copy()

    try:
        await mydrone.connect()
        await mydrone.telemetry_init()
        print("Connected to the flight controller")

        mydrone.load_modes_config()
        for mode_id in mydrone.modes:
            if mode_id not in mini_modes:
                mini_modes.append(mode_id)
        print('Modes bitmap:', mini_modes)

        while True:
            # Collect telemetry
            analog = mydrone.get_analog()
            modes = mydrone.get_board_modes()
            activemodes = [i for i, mode_id in enumerate(mini_modes) if mode_id in modes]
            modemap = list_to_int(activemodes)
            gpsd = mydrone.get_gps_data()
            speed = gpsd['speed']
            alt = mydrone.get_altitude()
            gps = froggeolib.GPSposition(gpsd['lat'], gpsd['lon'], alt)
            print(gps)
            if gps.lat == 0: gps.lat = 0.0001
            if gps.lon == 0: gps.lon = 0.0001
            if gps.alt == 0: gps.alt = 0.0001
            gyro = mydrone.get_attitude()
            full_mgrs = froggeolib.latlon_to_mgrs(gps.lat, gps.lon, precision=5)
            pos = froggeolib.encode_mgrs_binary(full_mgrs, precision=5)

            msg_enum = Messages.Status.System.INAV
            

            msg_id = messageid(msg_enum)
            payload = msg_enum.payload(
                airspeed=int(speed),
                inavmodes=modemap,
                groundspeed=int(speed),
                heading=int(gyro["yaw"]),
                msl_alt=int(alt),
                packed_mgrs=pos
            )

            # Send telemetry
            encoded_message = encode_message(msg_enum, payload)
            transport.send(encoded_message,"gcs1")
            print(f"[SENT] Telemetry message, length: {len(encoded_message)} bytes")

            # Receive messages
            messages = transport.receive()
            for msg in messages:
                try:
                    category, subcategory, message, payload = decode_message(msg["data"])
                    print(f"[RECEIVED] Message from {msg['from']}: {category}.{subcategory}.{message}")

                    if category == Messages.Command.value:
                        print(f"Command payload: {payload}")
                        # Handle commands here

                except Exception as e:
                    print(f"[RECEIVED] Error decoding message: {e}")

            await asyncio.sleep(SEND_INTERVAL)

    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt as e:
        print(f"Shut down")
    finally:
        mydrone.stop()
        if mesh_client:
            mesh_client.meshint.close()
        if sock:
            sock.close()
        print("Connection closed")

if __name__ == '__main__':
    asyncio.run(main())