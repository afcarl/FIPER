from __future__ import print_function, unicode_literals, absolute_import

import socket as sck

from FIPER.generic import CAR_PROBE_PORT, validate_car_tag
from FIPER.generic.interfaces import CarInterface, interface_factory
from FIPER.generic.abstract import AbstractListener, StreamDisplayer


class DirectConnection(AbstractListener):

    def __init__(self, myIP):
        super(DirectConnection, self).__init__(myIP, self._listener_callback)
        self.target = None
        self.interface = None  # type: CarInterface
        self.streamer = None  # type: StreamDisplayer

    def _listener_callback(self, msock):
        """
        This method is called by AbstractListener.run() on the newly
        created message-connection socket which creates the messaging
        channel between the remote car and this class.
        """
        self.interface = interface_factory(msock, self.dsocket, self.rcsocket)

    def connect(self, ip):
        """
        Coordinates the bootstrapping of a car-server connection.
        Groups together the following routines:
        - self._probe:
        -- sends a connect message to the car
        -- receives and validates 
        """
        self._probe(ip, "connect")

        self.run()

    def get_stream(self, bytestream=False):
        if self.interface is None:
            raise RuntimeError("No connection available!")
        stream = (self.interface.bytestream()
                  if bytestream else
                  self.interface.framestream())
        for d in stream:
            yield d

    def display_stream(self):
        if self.interface is None:
            print("DirectConnection: no interface!")
            return
        self.streamer = StreamDisplayer(self.interface)

    def stop_stream(self):
        self.streamer.teardown(1)

    @staticmethod
    def _probe(ip, msg):
        """
        Probes an IP address with a given message.
        This causes the remote car to send back its
        tag, which is validated, then the car ID is
        extracted from it and returned.
        """
        assert unicode(msg) in ("connect", "probe"), "Invalid message!"

        sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        try:
            sock.connect((ip, CAR_PROBE_PORT))
        except sck.error:
            print("DirectConnection: invalid address: ", ip)
            return

        sock.sendall(msg)
        tag = unicode(sock.recv(1024))
        ID = validate_car_tag(tag, ip)
        if ID is None:
            print("DirectConnection: invalid car ID from tag: {} @ {}"
                  .format(tag, ip))
            return
        return ID

    @staticmethod
    def probe(ip):
        return DirectConnection._probe(ip, b"probing")
