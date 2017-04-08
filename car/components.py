from __future__ import print_function, absolute_import, unicode_literals

import os
import abc
import time
import socket
import warnings
import threading as thr

import cv2

from FIPER.generic import CaptureDeviceMocker, DTYPE

DUMMY_VIDEOFILE = ""


class ComponentBase(object):

    __metaclass__ = abc.ABCMeta

    type = ""

    def __init__(self):
        self.sock = None
        self.running = False
        self.worker = None

    def connect(self, sock):
        sock.settimeout(1)
        self.sock = sock

    def start(self):
        if self.sock is None:
            print("{}: object unitialized! Please call connect(sock) first!"
                  .format(self.type))
            return
        if not self.running:
            self.worker = thr.Thread(target=self.run, name="Streamer")
            self.worker.start()

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)
        self.sock.close()
        self.worker = None


class RCReceiver(ComponentBase):

    type = "RCReceiver"

    def __init__(self):
        super(RCReceiver, self).__init__()
        self._recvbuffer = []
        print("RC: online")

    def run(self):
        while self.running:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                pass
            else:
                data = unicode(data)
                print("RC:", data)
                data = data.split(";")

                # # Push RC commands to hardware! # #
                self._recvbuffer.extend(data)     # #
                # # # # # # # # # # # # # # # # # # #

                # Clip the buffer, only keep the last 100 items
                self._recvbuffer = self._recvbuffer[-100:]
        print("RC: Exiting...")


class TCPStreamer(ComponentBase):

    """
    Abstraction of the video streamer.
    Factored out from TCPCar, this class enables
    switching the stream on and off in a managed way.
    """

    type = "TCPStreamer"

    def __init__(self):
        super(TCPStreamer, self).__init__()
        self._frameshape = None
        self.eye = Eye()
        self._determine_frame_shape()
        print("STREAMER: online")

    @property
    def frameshape(self):
        return str(self._frameshape)[1:-1].replace(", ", "x")

    def _determine_frame_shape(self):
        success, frame = self.eye.read()
        if not success:
            success, frame = self._fall_back_to_white_noise_stream()
        self._frameshape = frame.shape
        self.eye.close()

    def _fall_back_to_white_noise_stream(self):
        warnings.warn("Capture device unreachable, falling back to white noise stream!",
                      RuntimeWarning)
        self.eye = Eye(CaptureDeviceMocker)
        return self.eye.read()

    def frame(self):
        """Returns a single frame"""
        return self.eye.read()

    def run(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        pushed = 0
        self.running = True
        self.eye.open()
        while self.running:
            success, frame = self.frame()
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype(DTYPE).tostring()  #
            ##########################################
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.sock.send(slc)
                if not self.running:
                    break
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")
        self.eye.close()
        print("STREAMER: Stream terminated!")


class Eye(object):

    # noinspection PyArgumentList
    def __init__(self, dev=None):
        if dev is None:
            if not DUMMY_VIDEOFILE:
                self.device = lambda: cv2.VideoCapture(0)
            elif not os.path.exists(DUMMY_VIDEOFILE):
                self.device = CaptureDeviceMocker
            else:
                self.device = lambda: cv2.VideoCapture(DUMMY_VIDEOFILE)
        else:
            self.device = dev

        self._eye = None

    def open(self):
        self._eye = self.device()

    def read(self):
        if self._eye is None:
            self.open()
        return self._eye.read()

    def close(self):
        self._eye.release()
        self._eye = None
