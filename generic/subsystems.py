from __future__ import print_function, absolute_import, unicode_literals

import time
import socket
import threading as thr


class StreamDisplayer(thr.Thread):
    """
    Displays the video streams of cars.
    Instantiating this class instantly launches it
    in a separate thread.
    """

    # TODO: handle the cv2 display's close (X) button...
    # TODO: abstract this class. Discard the CarInterface
    # and remake this with a generator function as dependency

    def __init__(self, carint):
        """
        :param carint: CarInterface instance 
        """
        self.interface = carint
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = True
        print("STREAM_DISPLAYER: online")
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
        print("STREAM_DISPLAYER: Exiting...")

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running:
            self.teardown(sleep=1)


class Forwarder(object):

    def __init__(self, srcsock, trgsock, name=""):
        self.srcsock = srcsock
        self.trgsock = trgsock
        self.tag = name + "-Forwarder"
        self.worker = None
        self.working = False

    def start(self):
        if self.worker is not None:
            print("{}: already forwarding from {0[0]}:{0[1]} to {1[0]}:{1[1]}"
                  .format(self.tag, self.srcsock.getsockname(), self.trgsock.getsockname()))
            return
        self.worker = thr.Thread(target=self.run, name="ClientInterface-rc_job")
        self.worker.start()

    def run(self):
        print("{} starts working".format(self.tag))
        self.working = True
        while self.working:
            try:
                data = self.srcsock.recv(1024)
            except socket.timeout:
                pass
            else:
                self.trgsock.send(data)
        print("{} exiting...".format(self.tag))

    def teardown(self, sleep=1):
        self.working = False
        time.sleep(sleep)
        self.worker = None
