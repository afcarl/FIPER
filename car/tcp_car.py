from __future__ import print_function, absolute_import, unicode_literals

# STDLIB imports
import socket

# Project imports
from FIPER.car.components import TCPStreamer, RCReceiver, Idle
from FIPER.generic.messaging import Messaging
from FIPER.generic.const import (
    MESSAGE_SERVER_PORT, STREAM_SERVER_PORT, RC_SERVER_PORT
)


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

    def mainloop(self, srvIP=None):
        while 1:
            self.server_ip = None
            if srvIP is not None:
                self.server_ip = srvIP
                srvIP = None
            else:
                self._idle()  # sets server IP implicitly
            if self.server_ip:
                self._connect()
            else:
                return
            self._listen()

    def _idle(self):
        while 1:
            try:
                self.server_ip = Idle(self.ip, self.ID).mainloop()
            except KeyboardInterrupt:
                print("TCPCar IDLE: terminating!")
                break
            except Exception as E:
                print("TCPCar IDLE: caught exception:", E.message)
                print("TCPCar IDLE: ignoring!")
        print("TCPCar IDLE: exiting...")

    def _connect(self):
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

    def _listen(self):
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

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def shutdown(self, msg=None):
        if msg is not None:
            self.out(msg)
        if self.receiver is not None:
            self.receiver.teardown(0)
        if self.streamer is not None:
            self.streamer.teardown(0)
        if self.messenger is not None:
            self.messenger.send("offline")
            self.messenger.teardown(2)
        self.live = False
