from __future__ import print_function, absolute_import, unicode_literals

# Stdlib imports
import time

# Project imports
from FIPER.car.components import TCPStreamer, RCReceiver, Idle, Handshake, Ear
from FIPER.generic.messaging import Messaging
from FIPER.generic.const import STREAM_SERVER_PORT


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
        self.ear = None  # type: Ear
        self.live = False
        self.server_ip = None

    def mainloop(self, srvIP=None):
        """
        This method needs some more love
        
        :param srvIP: the IP address of the server 
        """
        self.server_ip = None
        if srvIP is not None:
            self.server_ip = srvIP
        else:
            self.out("No server IP supplied, going into IDLE state...")
            self._idle()  # sets server IP implicitly

        if self.server_ip:
            try:
                self._connect()
            except Exception as E:
                self.out("exception while connecting:", E)
                self.shutdown()
                return
        else:
            self.shutdown()
            return

    def _idle(self):
        while 1:
            try:
                self.server_ip = Idle(self.ip, self.ID).mainloop()
            except KeyboardInterrupt:
                self.out("IDLE terminated!")
                break
            except Exception:
                raise
            else:
                break
        self.out("IDLE exiting...")

    def _connect(self):
        """Establishes the messaging connection with a server"""
        self.messenger = Messaging.connect_to(
            self.server_ip, timeout=1,
            tag="{}-{}:".format(self.entity_type, self.ID).encode()
        )
        time.sleep(3)
        Handshake.perform(self.streamer, self.messenger)
        self.ear = Ear(self.messenger, stream=self.stream_command, shutdown=self.shutdown)
        self.out("connected to", self.server_ip)

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}:".format(self.ID), *args, sep=sep, end=end)

    def stream_command(self, where):
        if where == "on":
            self.streamer.connect(self.server_ip, STREAM_SERVER_PORT)
            self.streamer.start()
        elif where == "off":
            self.streamer.teardown(0.5)
        else:
            return

    def shutdown(self, msg=None):
        if msg is not None:
            self.out(msg)
        if self.receiver is not None:
            self.receiver.teardown(0)
        if self.streamer is not None:
            self.streamer.teardown(0)
        if self.messenger is not None:
            self.messenger.send(b"offline")
            self.messenger.teardown(2)
        self.live = False
