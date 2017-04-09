from __future__ import print_function, absolute_import, unicode_literals

import numpy as np

from .const import DTYPE
from .messaging import Messaging


def interface_factory(msock, dsock, rcsock):

    """
    Coordinates the handshake between a network entity
    (a Car or Client) and a listener server.
    This abstraction is required because either a central
    server (FleetHandler, see host/bridge.py) or a
    standalone client (DirectConnection, see client/direct.py
    has to be able to control a remote car on the network.
    
    :param msock: connected socket, connected to a remote car
    :param dsock: unconnected server socket awaiting data connections
    :param rcsock: unconnected server socket awaiting RC connections
    """

    def valid_introduction(intr):
        if ":HELLO;" in intr:
            return True
        print("LISTENER: invalid introduction!")
        return False

    def valid_frame_shape(fs):
        if len(fs) < 2 or len(fs) > 3:
            errmsg = ("Wrong number of dimensions in received frameshape definition.\n" +
                      "Got {} from {}!".format(ID, frameshape))
            print(errmsg)
            return False
        return True

    def parse_introductory_string(s):
        """
        Introduction looks like this:
        {entity_type}-{ID}:HELLO;{frY}x{frX}x{frC}
        """

        s = s.split(":HELLO;")
        etype, remoteID = s[0].split("-")

        if etype == "car":
            try:
                shp = [int(sp) for sp in s[1].split("x")]
            except ValueError:
                print("LISTENER: Received wrong frameshape definition from {}!\nGot {}"
                      .format(remoteID, introduction[1]))
                return None
        else:
            shp = None
        return etype, remoteID, shp

    messenger = Messaging(msock)
    introduction = None
    while introduction is None:
        introduction = messenger.recv(timeout=1)
        print("IFC_FACTORY: got introduction:", introduction)
    if not valid_introduction(introduction):
        return
    messenger.send(b"HELLO")
    result = parse_introductory_string(introduction)
    entity_type, ID = result[:2]
    if not result:
        return
    if entity_type == "car":
        frameshape = result[2]
        if not valid_frame_shape(frameshape):
            return
        if rcsock is None:
            print("INTERFACE: no rcsocket provided :(")
        ifc = CarInterface(
            ID, dsock, rcsock, messenger, frameshape
        )
    elif entity_type == "client":
        ifc = ClientInterface(
            ID, dsock, rcsock, messenger
        )
    else:
        raise RuntimeError("Unknown entity type: " + entity_type)
    return ifc


class NetworkEntity(object):
    """
    Base class for all connections,
    where Entity may be some remote network entity
    (like a car or a client).
    
    Groups together the following concepts:
    - a message-passing TCP channel implemented in generic.messaging
    - a one-way data connection, used to read or forward a data stream
    """

    entity_type = ""

    def __init__(self, ID, dlistener, rclistener, messenger):
        self.ID = ID
        self.messenger = messenger  # type: Messaging
        self.send = messenger.send
        self.recv = messenger.recv
        self.remote_ip = None
        self._accept_connection_and_validate_ip_addresses(dlistener, "Data")
        self._accept_connection_and_validate_ip_addresses(rclistener, "RC")

    def _accept_connection_and_validate_ip_addresses(self, sock, typ):
        conn, addr = sock.accept()
        self.out("{} connection from {}:{}".format(typ, *addr))
        if self.remote_ip:
            if self.remote_ip != addr[0]:
                msg = "Warning! Difference in inbound connection addresses!\n"
                msg += ("Messaging is on {}\nData is on {}\nRC is on {}"
                        .format(self.messenger.sock.getsockname()[0],
                                self.remote_ip, addr[0]))
                raise RuntimeError(msg)
        else:
            self.remote_ip = addr[0]
        if typ == "Data":
            self.dsocket = conn
        else:
            self.rcsocket = conn

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        # noinspection PyTypeChecker
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("{}IFACE {}: ".format(self.entity_type.upper(), self.ID),
              *args, sep=sep, end=end)

    def teardown(self, sleep):
        self.messenger.teardown(sleep)
        self.dsocket.close()


class CarInterface(NetworkEntity):

    """
    Abstraction of a Car-Server connection.
    Groups together two concepts:
    - the message connection, implemented by a Messaging object
    - the TCP data connection, used to receive an A/V stream
    """

    entity_type = "car"

    def __init__(self, ID, dlistener, rclistener, messenger, frameshape):
        """
        :param ID: the ID of the remote car 
        :param dlistener: serving TCP socket on STREAM_SERVER_PORT
        :param messenger: a Messaging instance (see generic.messaging)
        :param frameshape: string descriping the video frame shape: {}x{}x{}
        """

        super(CarInterface, self).__init__(ID, dlistener, rclistener, messenger)
        self.out("Frameshape:", frameshape)
        self.frameshape = frameshape

    def bytestream(self):
        """
        Simple generator yielding raw bytes from the data socket
        """
        yield self.dsocket.recv(1024)

    def framestream(self):
        """
        Generator function that yields the received video frames
        """
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
    - the message connection, implemented by a Messaging object
    - TCP or UDP or RTP connection, used to send the A/V stream
    """

    entity_type = "client"

    def __init__(self, ID, dlistener, rclistener, messenger):
        """
        :param ID: the client's unique ID
        :param dlistener: serving TCP socket on STREAM_SERVER_PORT
        :param messenger: Messaging object
        """
        super(ClientInterface, self).__init__(ID, dlistener, rclistener, messenger)
        self.worker = None
        self.target_carinterface = None
        self.streaming = False

    def teardown(self, sleep=3):
        self.streaming = False
        super(ClientInterface, self).teardown(sleep)
        self.worker = None
        self.out("Teardown finished!")
