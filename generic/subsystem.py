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

    # TODO: abstract this class. Discard the CarInterface dependecy

    def __init__(self, carint):
        """
        :param carint: CarInterface instance 
        """
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = False
        self.interface = carint
        self.start()

    def run(self):
        """
        Displays the remote car's stream with cv2.imshow()
        """
        import cv2
        stream = self.interface.framestream()
        print("STREAM_DISPLAYER: online")
        self.running = True
        for i, pic in enumerate(stream, start=1):
            # self.interface.out("\rRecieved {:>4} frames of shape {}"
            #                    .format(i, pic.shape), end="")
            cv2.imshow("{} Stream".format(self.interface.ID), pic)
            keypress = cv2.waitKey(10)
            if not self.running or keypress == 27:
                break
        cv2.destroyWindow("{} Stream".format(self.interface.ID))
        print("STREAM_DISPLAYER: Exiting...")
        self.teardown(0)

    def teardown(self, sleep=0):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running:
            self.teardown(sleep=1)


class Forwarder(object):

    def __init__(self, srcsock, trgsock, name=""):
        self.srcsock = srcsock
        self.trgsock = trgsock
        self.tag = "-".join((name, "Forwarder"))
        self.worker = None
        self.running = False

    def start(self):
        if self.worker is not None:
            print("{}: already forwarding from {0[0]}:{0[1]} to {1[0]}:{1[1]}"
                  .format(self.tag, self.srcsock.getsockname(), self.trgsock.getsockname()))
            return
        self.worker = thr.Thread(target=self.run, name="ClientInterface-rc_job")
        self.worker.start()

    def run(self):
        print("{} starts working".format(self.tag))
        self.running = True
        while self.running:
            try:
                data = self.srcsock.recv(1024)
            except socket.timeout:
                pass
            else:
                self.trgsock.send(data)
        print("{} exiting...".format(self.tag))

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)
        self.worker = None

    def __del__(self):
        if self.running:
            self.teardown()
