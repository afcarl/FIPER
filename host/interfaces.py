from __future__ import print_function

import socket

import numpy as np

from FIPER.generic import *


class NetworkEntity(object):
    """
    Abstraction of a server-someone connection
    """

    def __init__(self, ID, ip, messenger):
        # car_ID and framesize are sent throught the message socket
        self.ID = ID
        self.ip = ip
        self.messenger = messenger
        self.send = messenger.send
        self.recv = messenger.recv

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("IFACE {}: ".format(self.ID), *args, sep=sep, end=end)


class CarInterface(NetworkEntity):
    """
    Abstraction of a car-server connection.
    """

    def __init__(self, ID, srv_ip, dport, frameshape, messenger):
        super(CarInterface, self).__init__(ID=ID, ip=srv_ip, messenger=messenger)
        self.framesize = frameshape
        self.out("Framesize:", self.framesize)
        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dsocket.bind((srv_ip, dport))
        self.dsocket.listen(1)
        self.dsocket, (car_ip, car_port) = self.dsocket.accept()

    def get_stream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            data = data[datalen:]


class ClientInterface(NetworkEntity):
    pass
