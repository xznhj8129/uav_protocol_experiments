#!/usr/bin/env python3

"""
brokerless_meshtastic_msgpack.py

Demonstrates direct, brokerless messaging across a Meshtastic LoRa mesh,
using MessagePack (msgpack) for compact encoding of Python dictionaries.

Author: ChatGPT

Instructions:
1. Install dependencies:
   pip install meshtastic msgpack

2. Connect a Meshtastic device via USB (T-Beam, T-Echo, etc.) to your PC.
3. (Optional) Update SERIAL_PORT to match your device path ("/dev/ttyUSB0", "COM3", etc.).
4. (Optional) Set DEST_NODE_ID if you want to send unicast messages to a specific node ID.
   Leave it as None to broadcast to all nodes.

5. Run this script. Each instance will:
   - Send a compact MessagePack-encoded message every 15 seconds.
   - Print any received messages (decoded from MessagePack).
6. Run the same script on another machine with a second Meshtastic node
   to see them exchange messages in a fully distributed (no broker!) manner.
"""

import time
import msgpack
from frogtastic import *

SERIAL_PORT = '/dev/ttyACM0'
DEST_NODE_ID = '!336432b4'



link_port = 277


client = MeshtasticClient(SERIAL_PORT)
my_id = client.meshint.getMyNodeInfo()["user"]["id"]
nodes = nodes = client.meshint.nodes
print(f"[INIT] Connected to Meshtastic node. My node ID: 0x{my_id}")
def main():
    """
    1. Initialize Meshtastic Serial Interface
    2. Register receive callback
    3. Periodically send test messages (MessagePack-encoded)
    """

    # Create a Meshtastic interface to the local device

    counter = 0
    try:
        while True:
            message_dict = {
                "counter": counter,
                "text": "Hello from the brokerless Meshtastic mesh!",
                "timestamp": time.time()
            }

            messages = client.checkMail()
            for msg in messages:
                if msg["portnum"] == link_port:
                    try:
                        msg = msgpack.loads(raw_data, strict_map_key=False)
                    except Exception as e:
                        print(f"[RECEIVED] Unrecognized binary data fromId={msg.get('from')}. Error: {e}")
            
            encoded = msgpack.dumps(message_dict)

            client.meshint.sendData(b'[TestData]',portNum=258, wantAck=True) 

            counter += 1
            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Exiting script.")
        client.close()


if __name__ == "__main__":
    main()
