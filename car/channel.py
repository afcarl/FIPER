from __future__ import print_function, unicode_literals, absolute_import

import abc
import time
import socket
import warnings
import threading as thr

from FIPER.car.component import CaptureDevice, CaptureDeviceMocker
from FIPER.generic.const import DTYPE


class ChannelBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.sock = None
        self.running = False
        self.worker = None

    def connect(self, IP, port):
        self.sock = socket.create_connection((IP, port), timeout=1)

    def start(self):
        if self.sock is None:
            print("{}: object unitialized!".format(self.type))
            return
        if not self.running:
            print("Starting new {} thread!".format(self.type))
            self.worker = thr.Thread(target=self.run, name="Streamer")
            self.worker.start()

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError

    def cleanup(self, sleep=0):
        self.running = False
        time.sleep(sleep)
        if self.sock:
            self.sock.close()
        self.sock = None
        self.worker = None

    def teardown(self, sleep=0):
        self.cleanup(sleep)

    @property
    def type(self):
        return self.__class__.__name__


class RCReceiver(ChannelBase):
    """
    Handles the RC command receiving.
    Runs in separate thread, started in TCPCar._connect()
    """

    def __init__(self):
        super(RCReceiver, self).__init__()
        self._recvbuffer = []
        print("RC: online")

    def run(self):
        self.running = True
        while self.running:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                pass  # print("RC: Timed out!")
            else:
                data = data.decode("utf-8")
                data = data.split(";")
                print(", ".join(data), end=", ")

                # # # # # # # # # # # # # # # # # # #
                # TODO: write code for this!        #
                # Push RC commands to hardware      #
                # # # # # # # # # # # # # # # # # # #

                # Clip the buffer, only keep the last 100 items (?)
                self.cleanup()
                print("RCReceiver: socket closed, worker deleted! Exiting...")


class TCPStreamer(ChannelBase):
    """
    Abstraction of the video streamer.
    Factored out from TCPCar, this class enables
    switching the stream on and off in a managed way.

    Runs in a separate thread, started in TCPCar._listen()
    on a remote command from the controller.
    """

    def __init__(self):
        super(TCPStreamer, self).__init__()
        self._frameshape = None
        self.eye = CaptureDevice()
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
        warnings.warn("\nCapture device unreachable, falling back to white noise stream!",
                      RuntimeWarning)
        self.eye = CaptureDevice(CaptureDeviceMocker)
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
            for slc in (serial[i:i + 1024] for i in range(0, len(serial), 1024)):
                self.sock.send(slc)
                if not self.running:
                    break
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")
            self.eye.close()
            self.cleanup()
            print("TCPStreamer: socket and worker deleted! Exiting...")
