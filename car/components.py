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
        print("RCReceiver nice exit!")


class TCPStreamer(ComponentBase):

    """
    Abstraction of the video streamer.
    Factored out from TCPCar, this class enables
    switching the stream on and off in a managed way.
    """

    type = "TCPStreamer"

    def __init__(self):
        super(TCPStreamer, self).__init__()
        self.eye = None
        self._frameshape = None
        self._setup_capture_device()
        self._determine_frame_shape()

    @property
    def frameshape(self):
        return str(self._frameshape)[1:-1].replace(", ", "x")

    # noinspection PyArgumentList
    def _setup_capture_device(self):
        if not DUMMY_VIDEOFILE:
            self.eye = cv2.VideoCapture(0)
        elif not os.path.exists(DUMMY_VIDEOFILE):
            self.eye = CaptureDeviceMocker
        else:
            self.eye = cv2.VideoCapture(DUMMY_VIDEOFILE)

    def _determine_frame_shape(self):
        success, frame = self.eye.read()
        if not success:
            success, frame = self._fall_back_to_white_noise_stream()
        self._frameshape = frame.shape

    def _fall_back_to_white_noise_stream(self):
        warnings.warn("Capture device unreachable, falling back to white noise stream!",
                      RuntimeWarning)
        self.eye = CaptureDeviceMocker
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
        while self.running:
            success, frame = self.frame()
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype(DTYPE).tostring()  #
            ##########################################
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.sock.send(slc)
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")
        print("TCPStreamer: Stream terminated!")
