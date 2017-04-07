from __future__ import print_function, unicode_literals, absolute_import

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
    Base class for an entity which acts like a server,
    eg. client in DirectConnection and FleetHandler server.
    """

    def __init__(self, myIP, callback_on_connection):
        self.msocket = srvsock(myIP, "messaging", timeout=3)
        self.dsocket = srvsock(myIP, "stream")
        self.rcsocket = srvsock(myIP, "rc", timeout=1)
        self.running = False
        self.callback = callback_on_connection

    def run(self):
        try:
            self.mainloop()
        except:
            raise
        finally:
            self.teardown()

    def mainloop(self):
        while self.running:
            try:
                conn, addr = self.msocket.accept()
            except socket.timeout:
                pass
            else:
                print("\nABS_LISTENER: Received connection from {}:{}\n"
                      .format(*addr))
                self.callback(conn)
        self.teardown()

    def teardown(self, sleep=2):
        self.running = False
        time.sleep(sleep)
        self.msocket.close()
        self.dsocket.close()
        self.rcsocket.close()

    def __del__(self):
        if self.running:
            self.teardown(2)


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
