import asyncio
import socket
import warnings
import json
from typing import Optional, Dict, Any
import time
import crcmod
from protocol import SYNC_BYTE, crc16, encode_udp_packet, decode_udp_packet

class DatalinkInterface:
    def __init__(self, 
                 use_meshtastic: bool = False,
                 use_udp: bool = False,
                 wlan_device: Optional[str] = None,
                 radio_port: Optional[str] = None,
                 meshtastic_dataport: int = 260,
                 socket_host: str = '127.0.0.1',  # Default, will be overridden by nodemap
                 socket_port: int = 5555,         # Default, will be overridden by nodemap
                 my_name: str = "",
                 my_id: int = 0,
                 nodemap: Dict[str, Dict] = {}):
                 
        if not (use_meshtastic or use_udp):
            raise ValueError("At least one datalinks mode must be enabled.")
        
        self.use_meshtastic = use_meshtastic
        self.use_udp = use_udp
        self.radio_port = radio_port
        self.link_port = meshtastic_dataport
        self.my_name = my_name
        self.my_id = my_id
        self.nodemap = nodemap
        
        # Set socket host and port based on my_id from nodemap
        if my_id and my_id in nodemap:
            self.socket_host, self.socket_port = nodemap[my_id]["ip"]
        else:
            self.socket_host = socket_host
            self.socket_port = socket_port

        self.udp_sock = None
        self.mesh_client = None
        self.rx_buffer = []
        self.running = False
        self.loop = asyncio.get_event_loop()

    def start(self):
        if self.use_udp:
            print("DatalinkInterface using UDP")
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.setblocking(False)
            self.udp_sock.bind((self.socket_host, self.socket_port))

        if self.use_meshtastic:
            print("DatalinkInterface using Meshtastic")
            if not self.radio_port:
                raise ValueError("Radio port must be specified when using Meshtastic.")
            self.mesh_client = MeshtasticClient(self.radio_port)
        
        self.running = True
        asyncio.create_task(self._listen())
        print("Connected to datalinkss")

    def stop(self):
        self.running = False
        if self.udp_sock:
            self.udp_sock.close()
        if self.mesh_client:
            self.mesh_client.meshint.close()
        print("DatalinkInterfaces stopped")

    async def _listen(self):
        print(f"UDP Listening on {self.socket_host}:{self.socket_port}")
        while self.running:
            if self.use_udp and self.udp_sock:
                try:
                    data, addr = await self.loop.sock_recvfrom(self.udp_sock, 1024)
                    source, dest, data = decode_udp_packet(data)

                    if data:
                        self.rx_buffer.append({"data": data, "from": source})

                except Exception as e:
                    warnings.warn(f"Datalink UDP listen error: {str(e)}")
            await asyncio.sleep(0.25)

    def send(self, data: bytes, dest: Optional[str] = None, udp: bool = False, meshtastic: bool = False) -> bool:
        try:

            if self.use_udp and dest in self.nodemap and udp:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
                    send_sock.settimeout(2.0)

                    addr = self.nodemap[dest]["ip"]

                    #print(f"Sending to {dest} at {addr}")
                    encdat = encode_udp_packet(source=self.my_name, destination=dest, payload=data)
                    send_sock.sendto(encdat, tuple(addr))
            return True

        except Exception as e:
            warnings.warn(f"Datalink UDP Send failed: {str(e)}")
            return False

        try:
            if self.use_meshtastic and self.mesh_client and meshtastic:
                dest_meshid = "^all" if dest is None else self.nodemap[dest]["meshid"]
                self.mesh_client.meshint.sendData(
                    data,
                    destinationId=dest_meshid,
                    portNum=self.link_port,
                    wantAck=True
                )
        except Exception as e:
            warnings.warn(f"Datalink Meshtastic send failed: {str(e)}")
            return False

    def receive(self) -> list:
        if self.mesh_client is not None:
            for msg in self.mesh_client.checkMail() :
                if msg.get("port") == self.link_port:
                    self.rx_buffer.append(msg)

        messages = self.rx_buffer.copy()
        self.rx_buffer.clear()
        return messages

def load_nodes_map():
    with open("nodes.json", 'r') as file:
        return json.loads(file.read())

async def main():
    my_name = "gcs1"
    nodemap = load_nodes_map()
    my_id = nodemap[my_name][meshid]


    link_config = {
        "meshtastic": {
            "use": False,
            "radio_serial": '/dev/ttyACM0',
            "app_portnum": 260
        },
        "udp": {
            "use": True,
            "port": 5555,
            
        },

        "node_map": load_nodes_map()
    }
 
    datalinks = DatalinkInterface(
        use_meshtastic=link_config["meshtastic"]["use"],
        use_udp=link_config["udp"]["use"],
        my_id=my_id,
        nodemap=nodemap
    )

    datalinks.start()

    try:
        while True:
            msgs = datalinks.receive()
            if msgs:
                for msg in msgs:
                    print(f"Processed: {msg}")
            await asyncio.sleep(1)
    finally:
        datalinks.stop()

if __name__ == "__main__":
    asyncio.run(main())

