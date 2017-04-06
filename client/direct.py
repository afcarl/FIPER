from __future__ import print_function, unicode_literals, absolute_import

import socket as sck

from FIPER.generic import CAR_PROBE_PORT, Messaging
from FIPER.generic.interfaces import CarInterface


class DirectConnection(object):

    def __init__(self, remoteIP):
        self.target = remoteIP
        self.ifc = None  # type: CarInterface
        self.msocket = None
        self.dsocket = None
        self.rcsocket = None

    def _set_up_listener_sockets(self):
        self.msocket, self.dsocket, self.rcsocket = [
            sck.socket(sck.AF_INET, sck.SOCK_STREAM)
            for _ in range(3)
        ]

    def build_connection(self):
        """Bootstraps a CarInterface"""
        ID = self._probe_car_and_start_bootstrap_process()
        msngr = Messaging()


        self.ifc = CarInterface(ID, dlistener, rclistener, msngr, frameshape)

    def _probe_car_and_start_bootstrap_process(self):
        sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        sock.connect((self.target, CAR_PROBE_PORT))
        sock.sendall(b"connect")
        ID = unicode(sock.recv(1024))
        if not ID:
            raise RuntimeError("Invalid message from car: " + ID)
        return ID

