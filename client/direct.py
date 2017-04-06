from __future__ import print_function, unicode_literals, absolute_import

import socket as sck

from FIPER.generic import CAR_PROBE_PORT
from FIPER.generic.interfaces import CarInterface, interface_factory
from FIPER.generic.abstract import AbstractListener


class DirectConnection(AbstractListener, CarInterface):

    def __init__(self, myIP):
        AbstractListener.__init__(self, myIP, self._listener_callback)
        self.target = None
        self.ifc = None  # type: CarInterface
        self.messenger = None

    def _listener_callback(self, msock):
        self.interface = interface_factory(msock, self.dsocket, self.rcsocket)

    def build_connection(self, ip):
        """Bootstraps a CarInterface"""
        self.connect_target(ip)
        self.run()

    @staticmethod
    def _probe(ip, msg):
        sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        sock.connect((ip, CAR_PROBE_PORT))
        sock.sendall(msg)
        ID = unicode(sock.recv(1024))
        if not ID:
            raise RuntimeError("Invalid message from car: " + ID)
        return ID

    @staticmethod
    def connect_target(ip):
        return DirectConnection._probe(ip, b"connect")

    @staticmethod
    def probe_target(ip):
        return DirectConnection._probe(ip, b"probing")
