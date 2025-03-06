
from frogtastic import *
import froggeolib
import frogcot
import socket
import msgpack

class Transport:
    def __init__(self, mesh_client=None, sock=None, link_port=333, socket_port=5555):
        self.mesh_client = mesh_client
        self.sock = sock
        self.rx_buffer = []
        self.link_port = link_port
        self.socket_port = socket_port
        self.nodemap = {}
        #self.use_meshtastic = use_meshtastic
        #self.use_socket = use_socket

    def send(self, data, dest=None):
        if self.mesh_client is not None:

            dest_meshid = "^all" if dest is None else self.nodemap[dest]["meshid"]
            self.mesh_client.meshint.sendData( #**locals()
                bytes(data),
                destinationId=dest_meshid,
                portNum=self.link_port,
                wantAck=True
            )
        if self.sock is not None:
            self.sock.sendall(data)

    def receive(self):
        messages = []
        if self.mesh_client is not None:
            mesh_msgs = self.mesh_client.checkMail()
            if mesh_msgs is not None:
                for msg in mesh_msgs:
                    senderid = msg["senderid"]
                    if msg["port"] == self.link_port:
                        messages.append(msg)
        if self.sock is not None:
            try:
                data = self.sock.recv(1024)
                if data:
                    messages.append({"data": data, "from": "socket"})
            except BlockingIOError:
                pass  # No data available
        return messages