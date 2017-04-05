from __future__ import print_function, absolute_import, unicode_literals

# STDLIB imports
import time
import socket

# Project imports
from FIPER.generic import Messaging
from FIPER.generic import MESSAGE_SERVER_PORT, STREAM_SERVER_PORT, RC_SERVER_PORT
from FIPER.car.components import TCPStreamer, RCReceiver

DUMMY_VIDEOFILE = ""


class TCPCar(object):

    """
    A video streamer, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing.
    The TCPCar is implemented as a TCP client.
    """

    entity_type = "car"

    def __init__(self, ID, address, server_ip):
        self.ID = ID
        self.ip = address

        self.streamer = TCPStreamer()
        self.receiver = RCReceiver()
        self.messenger = None  # type: Messaging
        self.live = False

        self.connect(server_ip)

    def connect(self, server_ip):
        """Establishes connections with the server"""

        def setup_message_connection():
            msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msocket.connect((server_ip, MESSAGE_SERVER_PORT))
            self.messenger = Messaging(msocket, tag=b"{}-{}:".format(self.entity_type, self.ID))

        def setup_data_connection():
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.connect((server_ip, STREAM_SERVER_PORT))
            self.streamer.connect(dsocket)

        def setup_rc_connection():
            rcsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rcsock.settimeout(1)
            rcsock.connect((server_ip, RC_SERVER_PORT))
            self.receiver.connect(rcsock)

        def perform_handshake():
            introduction = "HELLO;" + self.streamer.frameshape
            self.messenger.send(introduction.encode())
            hello = None
            while hello is None:
                hello = self.messenger.recv(timeout=1)
                self.out("Received handshake:", hello)
            if hello != "HELLO":
                print("Wrong handshake from server! Shutting down!")
                raise RuntimeError("Handshake error!")

        # Function body starts here {just to be clear :)}
        setup_message_connection()
        perform_handshake()
        setup_data_connection()
        # setup_rc_connection()

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def shutdown(self, msg=None):
        if msg is not None:
            self.out(msg)
        if self.streamer is not None:
            self.streamer.running = False
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
        self.live = True
        while self.live:
            msg = self.messenger.recv(timeout=1)
            if msg is None:
                continue
            self.out("Received message:", msg)
            if msg == "shutdown":
                self.shutdown()
                break
            elif msg == "stream on":
                self.streamer.start()
            elif msg == "stream off":
                self.streamer.running = False
            else:
                self.out("Received unknown command:", msg)
        self.out("Shutting down...")
