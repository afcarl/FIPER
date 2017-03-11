from __future__ import print_function

import socket

import numpy as np

from FIPER.generic import *


class NetworkEntity(object):
    """Abstraction of a server-someone connection"""

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


class CarInterFaceBase(NetworkEntity):
    """
    Abstraction of a car-server connection.
    """

    def __init__(self, ID, ip, frameshape, messenger):
        super(CarInterFaceBase, self).__init__(ID=ID, ip=ip, messenger=messenger)
        self.framesize = frameshape
        self.out("Framesize:", self.framesize)
        self.dsocket = None

    def get_stream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            data = data[datalen:]


class UDPMixin(object):
    """
    Handles message-passing and stream receiving via UDP.
    """

    def __init__(self, srv_ip, port):
        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dsocket.bind((srv_ip, port))


class TCPMixin(object):
    """
    Handles message-passing and stream receiving via TCP.
    """

    def __init__(self, cli_ip, port):
        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dsocket.connect((cli_ip, port))


class ClientInterface(NetworkEntity):
    pass
