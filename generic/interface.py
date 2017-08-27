from __future__ import print_function, absolute_import, unicode_literals

import abc
import time
import socket
from threading import Thread

import numpy as np

from .const import DTYPE
from .abstract import AbstractCommander
from .messaging import Messaging
from .subsystem import Forwarder


class InterfaceFactory(object):

    """
    Coordinates the handshake between a network entity
    (a Car or Client) and a listener server.
    This abstraction is required because either a central
    server (FleetHandler, see host/bridge.py) or a
    standalone client (DirectConnection, see client/direct.py
    has to be able to connect to a remote car on the network.
    """

    def __init__(self, msock, dlistener, rclistener, recv_retries=10):
        """
        :param msock: connected socket, connected to a remote car
        :param dlistener: unconnected server socket awaiting data connections
        :param rclistener: unconnected server socket awaiting RC connections
        """

        self.messenger = Messaging(msock)
        self.dlistener = dlistener
        self.rclistener = rclistener
        self.introduction = None
        self.parsed = None
        self.etype = None
        self.ID = None
        self.info = None
        self.retries = recv_retries

    def get(self):
        if not self._read_introduction():
            return
        if not self._valid_introduction():
            print("IFC_BUILDER: invalid introduction @ validation:", self.introduction)
            return
        self.messenger.send(b"HELLO")
        if not self._parse_introductory_string():
            print("IFC_BUILDER: invalid introduction @ parsing:", self.introduction)
            return
        print("IFC_BUILDER: valid introduction!")
        return self._instantiate_interface()

    @property
    def _args(self):
        return self.ID, self.dlistener, self.rclistener, self.messenger, self.info

    def _read_introduction(self):
        tries = 0
        while self.introduction is None:
            self.introduction = self.messenger.recv(timeout=1)
            tries += 1
            if tries > self.retries:
                print("IFC_BUILDER: didn't receive an introduction!")
                return False
        return True

    def _valid_introduction(self):
        if ":HELLO;" in self.introduction:
            return True
        return False

    def _valid_frame_shape(self, framestring):
        try:
            frameshape = [int(sp) for sp in framestring.split("x")]
        except TypeError:
            return False
        if len(frameshape) not in (2, 3):
            return False
        self.info = frameshape
        return True

    def _parse_introductory_string(self):
        """
        Introduction looks like this:
        {entity_type}-{ID}:HELLO;{frY}x{frX}x{frC}
        """

        handshake, info = self.introduction.split(":HELLO;")
        self.etype, self.ID = handshake.split("-")

        if self.etype == "car" and not self._valid_frame_shape(info):
            return False
        return True

    def _instantiate_interface(self):
        ifc = {"car": _CarInterface,
               "client": _ClientInterface
               }[self.etype](*self._args)
        return ifc


class _Interface(object):

    """
    Base class for all connections,
    where Entity may be some remote network entity
    (like a car or a client).

    Groups together the following concepts:
    - a message-passing TCP channel implemented in generic.messaging
    - a one-way data connection, used to read or forward a data stream
    """

    __metaclass__ = abc.ABCMeta

    entity_type = ""

    def __init__(self, ID, dlistener, rclistener, messenger):
        self.ID = ID
        self.messenger = messenger
        self.send = messenger.send
        self.recv = messenger.recv
        self.remote_ip = None
        self.initiated = False
        try:
            self._accept_connection_and_validate_ip_addresses(dlistener, "Data")
            self._accept_connection_and_validate_ip_addresses(rclistener, "RC")
        except socket.timeout:
            self.initiated = False
        else:
            self.initiated = True

    def _accept_connection_and_validate_ip_addresses(self, sock, typ):
        self.out("Awaiting {} connection...".format(typ))
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
        self.rcsocket.close()


class _CarInterface(_Interface):

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

        super(_CarInterface, self).__init__(ID, dlistener, rclistener, messenger)
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

    def perform_remote_shutdown(self, await_remote=2):
        self.send(b"shutdown")
        time.sleep(await_remote)
        status = self.recv()
        errcode = status if status is None else (status == "car-{}:offline".format(self.ID))
        msgs = {None: "no corpse response",
                True: "shut down as expected",
                False: "unknown status"}
        print("CARIFC-{}: {}".format(self.ID, msgs[errcode]))
        return errcode

    def teardown(self, sleep=3):
        success = self.perform_remote_shutdown(await_remote=2)
        super(_CarInterface, self).teardown(max(0, sleep-2))
        self.out("Teardown finished!")
        return success

    def __del__(self):
        self.teardown()


class _ClientInterface(_Interface):

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
        super(_ClientInterface, self).__init__(ID, dlistener, rclistener, messenger)
        self.stream_worker = None
        self.rc_worker = None
        self.carifc = None
        self.state = state
        self.commander = self.__class__.Commander(
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
        super(_ClientInterface, self).teardown(sleep)

    def __del__(self):
        self.teardown()

    class Commander(Thread, AbstractCommander):

        """
        Nested class, which defines the command parser.
        Commands are received from the client's messaging channel.
        """

        def __init__(self, messenger, master_name, **commands):
            Thread.__init__(self, name=master_name + "-Commander")
            AbstractCommander.__init__(self, master_name, **commands)
            self.messenger = messenger  # type: Messaging

        def read_cmd(self):
            found = self.messenger.recv(1, timeout=1)
            if found is None:
                return "idle", ""
            found = found.split(" ")
            cmd = found[0].lower()
            args = found[1:] if len(found) > 1 else ""
            return cmd, args
