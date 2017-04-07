from __future__ import print_function, unicode_literals, absolute_import

import abc
import time
import socket
import threading as thr

from . import srvsock


# My experiment, do not use yet :)
# class SingletonMeta(type):
#
#     children = []
#
#     def __new__(mcs, **kwargs):
#         if mcs in SingletonMeta.children:
#             print("SingletonMeta: attempted to instantiate a Singleton again!")
#             return None
#         SingletonMeta.children.append(mcs)
#         return mcs.__new__(mcs, **kwargs)


class AbstractListener(object):
    """
    Abstract base class for an entity which acts like a server,
    eg. client in DirectConnection and FleetHandler server.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, myIP, callback_on_connection):
        """
        Listens for entities on the local network.
        Incomming connections produce a connected socket,
        on which callback_on_connection is called, so
        callback_on_connection's signature should look like so:
        callback(msock), where msock will be the connected socket.
        """
        self.msocket = srvsock(myIP, "messaging", timeout=3)
        self.dsocket = srvsock(myIP, "stream")
        self.rcsocket = srvsock(myIP, "rc", timeout=1)
        self.running = False
        self.callback = callback_on_connection

    def run(self):
        """
        Managed run, mainly intended to use in a separate thread
        """
        try:
            self.mainloop()
        except:
            raise
        finally:
            self.teardown()

    def mainloop(self):
        """
        Unmanaged run for e.g. one-time connection bootstrapping
        """
        self.running = True
        while self.running:
            try:
                conn, addr = self.msocket.accept()
            except socket.timeout:
                print("ABS_LISTENER: timeout!")
            else:
                print("ABS_LISTENER: Received connection from {}:{}"
                      .format(*addr))
                self.callback(conn)

    def teardown(self, sleep=2):
        print("AL: teardown")
        self.running = False
        time.sleep(sleep)
        self.msocket.close()
        self.dsocket.close()
        self.rcsocket.close()

    def __del__(self):
        print("AL: deconstructed :(")
        if self.running:
            self.teardown(2)


class AbstractProbe(object):
    """
    Mixin class for entities with probing capabilities.
    """


class StreamDisplayer(thr.Thread):

    """
    Displays the video streams of cars.
    Instantiating this class instantly launches it
    in a separate thread.
    """

    # TODO: handle the cv2 display's close (X) button...

    def __init__(self, carint):
        """
        :param carint: CarInterface instance 
        """
        self.interface = carint
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = True
        self.online = True
        self.start()

    def run(self):
        """
        Displays the remote car's stream with cv2.imshow()
        """
        import cv2
        stream = self.interface.framestream()
        for i, pic in enumerate(stream, start=1):
            # self.interface.out("\rRecieved {:>4} frames of shape {}"
            #                    .format(i, pic.shape), end="")
            cv2.imshow("{} Stream".format(self.interface.ID), pic)
            cv2.waitKey(1)
            if not self.running:
                break
        cv2.destroyWindow("{} Stream".format(self.interface.ID))
        self.online = False

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running or self.online:
            self.teardown(sleep=1)
