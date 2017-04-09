from __future__ import print_function, absolute_import, unicode_literals

# STDLIB imports
import time
import socket

# Project imports
from FIPER.car.components import TCPStreamer, RCReceiver
from FIPER.generic.messaging import Messaging
from FIPER.generic.const import (
    CAR_PROBE_PORT, MESSAGE_SERVER_PORT,
    STREAM_SERVER_PORT, RC_SERVER_PORT
)


class Idle(object):

    """Before instantiating TCPCar"""

    def __init__(self, myIP, myID):
        self.IP = myIP
        self.ID = myID
        self.sock = None
        self.conn = None
        self.remote_address = None

    def _setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.bind((self.IP, CAR_PROBE_PORT))
        self.sock.listen(1)
        print("CAR-{}: Awaiting connection... Hit Ctrl-C to break!".format(self.ID))

    def _read_message_from_probe(self):
        try:
            m = self.conn.recv(1024)
        except socket.timeout:
            return
        else:
            return m if m in ("probing", "connect") else None

    def _new_connection_causes_loopbreak(self):
        print("IDLE: probed by", self.IP)

        msg = self._read_message_from_probe()
        if msg is None:
            print("IDLE: unknown host:", self.remote_address[0])
            return False

        print("IDLE: got msg:", msg)
        self._respond_to_probe(msg)
        return msg == "connect"

    def _respond_to_probe(self, msg):
        m = b"car-{} @ {}".format(self.ID, self.IP)
        if msg in ("connect", "probing"):
            self.conn.send(m)
        else:
            print("IDLE: invalid message received! Ignoring...")

    def mainloop(self):
        self._setup_socket()
        while 1:
            try:
                self.conn, self.remote_address = self.sock.accept()
            except socket.timeout:
                pass
            else:
                if self._new_connection_causes_loopbreak():
                    break
                self.conn.close()
                self.conn = None
        return self.remote_address[0]


class TCPCar(object):

    """
    A video streamer, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing.
    The TCPCar is implemented as a TCP client.
    """

    entity_type = "car"

    def __init__(self, myID, myIP):
        self.ID = myID
        self.ip = myIP

        self.streamer = TCPStreamer()
        self.receiver = RCReceiver()
        self.messenger = None  # type: Messaging
        self.live = False
        self.server_ip = None
        self.idle()
        self.connect()

    def idle(self):
        self.server_ip = Idle(self.ip, self.ID).mainloop()

    def connect(self):
        """Establishes connections with the server"""

        def perform_handshake():
            send_indtroduction()
            hello = read_response()
            validate_response(hello)

        def send_indtroduction():
            introduction = "HELLO;" + self.streamer.frameshape
            self.messenger.send(introduction.encode())

        def read_response():
            for i in range(4, -1, -1):
                hello = self.messenger.recv(timeout=1)
                if hello is not None:
                    break
            else:
                # noinspection PyUnboundLocalVariable
                raise RuntimeError("Handshake error: {}".format(hello))
            return hello

        def validate_response(hello):
            if hello != "HELLO":
                print("Wrong handshake from server! Shutting down!")
                raise RuntimeError("Handshake error!")

        # Function body starts here {just to be clear :)}
        self.messenger = Messaging(
            socket.create_connection((self.server_ip, MESSAGE_SERVER_PORT), timeout=1),
            tag=b"{}-{}:".format(self.entity_type, self.ID)
        )
        perform_handshake()
        self.streamer.connect(
            socket.create_connection((self.server_ip, STREAM_SERVER_PORT))
        )
        self.receiver.connect(
            socket.create_connection((self.server_ip, RC_SERVER_PORT), timeout=1)
        )

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def shutdown(self, msg=None):
        if msg is not None:
            self.out(msg)
        if self.streamer is not None:
            self.streamer.teardown(1)
        if self.messenger is not None:
            self.messenger.send("offline")
            time.sleep(1)
            self.messenger.teardown()
        self.live = False

    def mainloop(self):
        """
        This loop wathces the messaging system and receives
        control commands from the server.
        """

        def read_a_single_message():
            m = self.messenger.recv(timeout=1)
            if m is None:
                return
            self.out("Received message:", m)
            return m

        self.live = True
        while self.live:
            msg = read_a_single_message()
            if msg is None:
                continue
            elif msg == "stream on":
                self.streamer.start()
            elif msg == "stream off":
                self.streamer.teardown(sleep=0.5)
            elif msg == "shutdown":
                self.shutdown()
                break
            else:
                self.out("Received unknown command:", msg)
        self.out("Shutting down...")
