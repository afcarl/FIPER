from __future__ import print_function, unicode_literals, absolute_import

import threading as thr

from FIPER.generic.abstract import AbstractListener, AbstractCommander
from FIPER.generic.interface import InterfaceBuilder


class Listener(AbstractListener):

    """
    Listens for incoming car connections for the server.
    Runs in a separate thread.
    """

    def __init__(self, master):
        AbstractListener.__init__(self, master.ip)
        self.master = master
        self.worker = None

    def start(self):
        """
        Creates a new worker thread in case Listener needs to be
        restarted.
        self.run is inherited from AbstractListener
        """
        if self.worker is not None:
            print("ABS_LISTENER: Attempted start while already running!")
            return
        self.worker = thr.Thread(target=self.mainloop, name="Server-Listener")
        self.worker.start()

    def teardown(self, sleep=2):
        super(Listener, self).teardown(sleep)
        self.worker = None

    def callback(self, msock):
        """
        Builds an interface and puts it into the server's appropriate
        container for later usage.
        :param msock: connected socket used for message connection
        """
        print("LISTENER: called callback on incoming connection!")
        ifc = InterfaceBuilder(msock, self.dlistener, self.rclistener).get()
        if not ifc:
            print("LISTENER: no interface received!")
            return
        print("LISTENER: received {} interface: {}".format(ifc.entity_type, ifc))
        if ifc.entity_type == "car":
            self.master.cars[ifc.ID] = ifc
        else:
            self.master.clients[ifc.ID] = ifc


class Console(AbstractCommander):

    def read_cmd(self):
        c = raw_input(self.prompt).split(" ")
        cmd = c[0].lower()
        if len(c) > 1:
            args = c[1:]
        else:
            args = []
        return cmd, args
