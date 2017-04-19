from __future__ import print_function, absolute_import, unicode_literals

from threading import Thread

import numpy as np

from .const import DTYPE
from .messaging import Messaging
from .abstract import AbstractEntity, AbstractConsole
from generic.subsystems import Forwarder


class _Commander(Thread, AbstractConsole):

    def __init__(self, messenger, master_name, **commands):
        Thread.__init__(self, name=master_name + "-Commander")
        AbstractConsole.__init__(self, master_name, **commands)
        self.messenger = messenger  # type: Messaging

    def read_cmd(self):
        found = self.messenger.recv(1, timeout=1)
        if found is None:
            return "idle", ""
        found = found.split(" ")
        cmd = found[0].lower()
        args = found[1:] if len(found) > 1 else ""
        return cmd, args


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
        frameshape = result[-1]
        if not valid_frame_shape(frameshape):
            return
        ifc = CarInterface(
            ID, dsock, rcsock, messenger, frameshape
        )
    elif entity_type == "client":
        status = result[-1]
        if status not in ("active", "passive"):
            return
        ifc = ClientInterface(
            ID, dsock, rcsock, messenger, status
        )
    else:
        raise RuntimeError("Unknown entity type: " + entity_type)
    return ifc


class CarInterface(AbstractEntity):

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


class ClientInterface(AbstractEntity):

    """
    Abstraction of a Client-Server connection.
    Groups together two concepts:
    - the message connection, implemented by a Messaging object
    - TCP or UDP or RTP connection, used to send the A/V stream
    """

    entity_type = "client"

    def __init__(self, ID, dlistener, rclistener, messenger, state):
        """
        :param ID: the client's unique ID
        :param dlistener: serving TCP socket on STREAM_SERVER_PORT
        :param messenger: Messaging object
        """
        super(ClientInterface, self).__init__(ID, dlistener, rclistener, messenger)
        self.stream_worker = None
        self.rc_worker = None
        self.carifc = None
        self.state = state
        self.commander = _Commander(
            messenger, master_name="CarIfc-{}".format(ID),
            shutdown=self.teardown,
            cars=lambda: "Lightning McQueen",
            connect=self.attach,
            disconnect=self.detach
        )
        self.commander.start()

    def attach(self, carifc):
        if self.carifc is not None:
            print("ClientInterface already connected to", self.carifc.ID)
            return
        self.carifc = carifc
        self.stream_worker = Forwarder(carifc.dsocket, self.dsocket, name="CliFace-Stream")
        self.rc_worker = Forwarder(carifc.rcsocket, self.rcsocket, name="CliFace-RC")
        self.send(b"x".join(bytes(d) for d in carifc.frameshape))

    def forward(self):
        if self.carifc is None:
            print("No CarInterface connected!")
            return
        self.stream_worker.start()
        if self.state == "active":
            self.rc_worker.start()

    def detach(self):
        if self.carifc is None:
            return
        self.stream_worker.teardown(0)
        self.rc_worker.teardown(1)
        self.carifc = None

    def teardown(self, sleep=1):
        if self.carifc:
            self.detach()
        self.commander.teardown()
        super(ClientInterface, self).teardown(sleep)

    def __del__(self):
        self.teardown()
