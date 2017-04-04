from __future__ import print_function, absolute_import, unicode_literals

import time
import threading as thr

import numpy as np

from FIPER.generic import *


class NetworkEntity(object):
    """
    Base class for all Server-Entity connections,
    where Entity may be some remote network entity
    (like a car or a client).
    
    Groups together the following concepts:
    - a message-passing TCP channel implemented in by generic.messaging
    - a one-way data connection, used to read or forward a data stream
    """

    entity_type = ""

    def __init__(self, ID, dlistener, messenger):
        self.ID = ID
        self.messenger = messenger
        self.send = messenger.send
        self.recv = messenger.recv
        time.sleep(1)
        conn, addr = dlistener.accept()
        self.out("Data connection established with {} @ {}:{}"
                 .format(self.entity_type, *addr))
        self.dsocket = conn
        self.remote_ip, self.remote_port = addr

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        # noinspection PyTypeChecker
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("{}IFACE {}: ".format(self.entity_type.upper(), self.ID),
              *args, sep=sep, end=end)

    def teardown(self, sleep):
        self.messenger.teardown(sleep)
        self.dsocket.close()

    def __del__(self):
        self.teardown(3)


class CarInterface(NetworkEntity):

    """
    Abstraction of a Car-Server connection.
    Groups together two concepts:
    - the message connection, implemented by a Messaging object
    - the TCP data connection, used to receive an A/V stream
    """

    entity_type = "car"

    def __init__(self, ID, dlistener, messenger, frameshape):
        super(CarInterface, self).__init__(ID, dlistener, messenger)

        self.frameshape = tuple(int(fs) for fs in frameshape.split("x"))
        self.out("Framesize:", frameshape)

    def bytestream(self):
        """
        Simple generator yielding raw bytes from the data socket
        """
        yield self.dsocket.recv(1024)

    def framestream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.frameshape)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            # Car RPM data is not yet transmitted.
            # It is intended to be the last [n] byte of <data>

            # time.sleep(1. / fps)  # set FPS -> this is not right
            # we need timestamps for the frames.

            # # # # FRAME PREPROCESSING SHOULD BE DONE HERE # # # #
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.frameshape)
            # #####################################################
            data = data[datalen:]

    def teardown(self, sleep=3):
        super(CarInterface, self).teardown(sleep)
        self.out("Teardown finished!")


class ClientInterface(NetworkEntity):

    """
    Abstraction of a Client-Server connection.
    Groups together two concepts:
    
    """

    entity_type = "client"

    def __init__(self, ID, dlistener, messenger):
        super(ClientInterface, self).__init__(ID, dlistener, messenger)
        self.worker = None
        self.target_carinterface = None
        self.streaming = False

    def teardown(self, sleep=3):
        self.streaming = False
        super(ClientInterface, self).teardown(sleep)
        self.worker = None
        self.out("Teardown finished!")


class ClientCarInterface(object):

    """
    Abstraction of a server-level Client-Car connection
    """

    def __init__(self, carifc, cliifc):
        self.carifc = carifc
        self.cliifc = cliifc
        self.stream_worker = None
        self.rc_worker = None
        self.streaming = False
        self.controlling = False

    def forward_stream(self):
        self.stream_worker= thr.Thread(target=self._forward_job)
        self.streaming = True
        self.stream_worker.start()

    def _forward_job(self):
        stream = self.carifc.bytestream()
        for byte in stream:
            self.cliifc.dsocket.send(byte)
            if not self.streaming:
                break
        self.streaming = False

    def _forward_rc(self):
        stream = self.cliifc.bytestream()
        for byts in stream:
            self.carifc.rcocket.send(byts)
            if not self.controlling:
                break
        self.controlling = False