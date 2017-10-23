from __future__ import print_function, absolute_import, unicode_literals

# Project imports
from FIPER.car.channel import TCPStreamer, RCReceiver
from FIPER.car.component import Commander
from FIPER.generic.messaging import Messaging


class TCPCar(object):

    """
    A video streamer, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing.
    The TCPCar is implemented as a TCP client.
    """

    entity_type = "car"

    def __init__(self, myID):
        self.ID = myID

        self.streamer = TCPStreamer()
        self.receiver = RCReceiver()
        self.messenger = None  # type: Messaging
        self.commander = None  # type: Commander
        self.online = False

    def run(self, server_ip):
        """Establishes the messaging connection with a server"""
        mytag = "{}-{}:".format(self.entity_type, self.ID).encode()
        self.messenger = Messaging.connect_to(server_ip, timeout=1, tag=mytag)
        self.receiver.connect(server_ip)
        self.receiver.start()
        self.streamer.connect(server_ip)
        self.commander = Commander(
            self.messenger, stream=self.stream_command, shutdown=self.shutdown
        )
        self.out("connected to", server_ip)
        self.commander.mainloop()

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}:".format(self.ID), *args, sep=sep, end=end)

    def stream_command(self, switch):
        if switch == "on":
            self.streamer.start()
        elif switch == "off":
            self.streamer.stop()
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
        self.online = False
