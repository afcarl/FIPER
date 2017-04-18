from __future__ import print_function, absolute_import, unicode_literals

import socket

from FIPER.generic.messaging import Messaging
from FIPER.generic.const import (
    MESSAGE_SERVER_PORT, STREAM_SERVER_PORT, RC_SERVER_PORT
)


class ServerConnection(object):

    entity_type = "client"

    def __init__(self, serverIP, ID):
        self.ID = ID
        self.serverIP = serverIP
        self.messaging = Messaging(
            socket.create_connection((serverIP, MESSAGE_SERVER_PORT))[0],
            tag=b"{}-{}:".format(self.entity_type, self.ID))

        # Validation should be done via the messaging channel:
        # - username/password check
        # - version check?
        # - server validation?

        self.dsocket = socket.create_connection((serverIP, STREAM_SERVER_PORT))[0]
        self.rcsocket = socket.create_connection((serverIP, RC_SERVER_PORT))[0]

    def _sendcmd(self, cmd, timeout=3):
        self.messaging.send(cmd)
        response = self.messaging.recv(timeout=timeout)
        return response

    def request_car_list(self):
        cars = self._sendcmd(b"cmd|cars", 3).split(", ")
        print(cars)
        return cars.split(", ")

    def request_car_connection(self, carID):
        status = self._sendcmd(b"cmd|connect {}".format(carID), 3)
        print("DIRECT_CONN: status received:", status)

    def observe_someone_else(self, ID):
        status = self._sendcmd(b"cmd|watch {}".format(ID), 3)
        print("DIRECT_CONN: status received:", status)
