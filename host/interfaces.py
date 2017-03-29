from __future__ import print_function, absolute_import, unicode_literals

import numpy as np
import time

from FIPER.generic import *


class NetworkEntity(object):
    """
    Abstraction of a server-entity connection,
    where entity may be a car or a client.
    """

    def __init__(self, ID, messenger):
        self.ID = ID
        self.messenger = messenger
        self.send = messenger.send
        self.recv = messenger.recv

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("IFACE {}: ".format(self.ID), *args, sep=sep, end=end)


class CarInterface(NetworkEntity):
    """
    Abstraction of a server-car connection.
    Groups together two concepts:
    - the message connection
    - the data connection, used for the A/V stream
    and defines the interface to use these
    """

    def __init__(self, ID, conn, frameshape, messenger):
        super(CarInterface, self).__init__(ID=ID, messenger=messenger)
        self.dsocket = conn
        print("CarInterface conn:")
        self.framesize = frameshape
        self.out("Framesize:", self.framesize)
        time.sleep(3)

    def get_stream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            # # # # FRAME PREPROCESSING SHOULD BE DONE HERE # # # #
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            # #####################################################
            data = data[datalen:]

    def teardown(self):
        self.messenger.teardown()
        self.dsocket.close()
        self.out("Teardown finished!")


class ClientInterface(NetworkEntity):
    pass
