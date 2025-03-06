import time
import socket
from frogtastic import MeshtasticClient
import froggeolib
from unavlib.modules.utils import inavutil
from message_structure import Messages
from protocol import *
from transport import Transport

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

RADIO_PORT = '/dev/ttyACM0'
LINK_PORT = 260
modemap = [27, 10, 12, 38, 0, 1, 53, 11, 31, 47]
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5555 
MY_ID = "gcs1"

# Transport configuration
USE_MESHTASTIC = True
USE_SOCKET = False

# Initialize transports
mesh_client = MeshtasticClient(RADIO_PORT) if USE_MESHTASTIC else None
sock = None
if USE_SOCKET:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

transport = Transport(mesh_client=mesh_client, sock=sock)
print("Connected to transports")
if mesh_client:
    print(mesh_client.meshint.getMyNodeInfo())

def int_to_list(bitmap):
    return [i for i in range(bitmap.bit_length()) if (bitmap & (1 << i)) != 0]

command_queue = [
    {
        "dest": "drone1",
        "msgid": messageid(Messages.Command.Mission.NAVIGATE_TO),
        "data": {"mgrs": "18TWL12345678"},
        "frequency": None # if none, send once
    }
]

try:
    while True:
        msgs = transport.receive()
        if msgs:
            for msg in msgs:
                try:
                    print(f"\n[RECEIVED] Message at {time.time():.1f}")
                    print(f"From: {msg['senderid']}")
                    print(msg)
                    msgid, data = decode_message(msg["data"])
                    print("MSG ID:", msgid)
                    data["packed_mgrs"] = froggeolib.decode_mgrs_binary(data["packed_mgrs"],precision=5)
                    for key, value in data.items():
                        print(f"\t{key}: {value}")

                    data["pos"] = froggeolib.mgrs_to_latlon(data["packed_mgrs"])

                    modes = int_to_list(data["inavmodes"])
                    activemodes = []
                    for i in modes:
                        activemodes.append(modemap[i])
                    print('Modes:',[inavutil.modesID.get(i) for i in activemodes])


                except Exception as e:
                    print(f"Error decoding message: {e}")

        # Send a NAVIGATE_TO command (example)




        time.sleep(1)

except KeyboardInterrupt as e:
    print(f"Shut down")
finally:
    if mesh_client:
        mesh_client.meshint.close()
    if sock:
        sock.close()
    print("Connection closed")