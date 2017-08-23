from __future__ import print_function, unicode_literals, absolute_import

import abc
import time
import socket
import threading as thr

from FIPER.car.component import CaptureDevice, CaptureDeviceMocker
from FIPER.generic.const import DTYPE, FPS, STREAM_SERVER_PORT, RC_SERVER_PORT


class ChannelBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.sock = None
        self.running = False
        self.worker = None

    def _connectbase(self, IP, port, timeout):
        self.sock = socket.create_connection((IP, port), timeout=timeout)

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

    def stop(self):
        self.running = False
        self.worker = None

    def teardown(self, sleep=0):
        self.stop()
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        time.sleep(sleep)

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

    def connect(self, IP):
        super(RCReceiver, self)._connectbase(IP, RC_SERVER_PORT, timeout=1)
        print("RCRECEIVER: connected to {}:{}".format(IP, RC_SERVER_PORT))

    def run(self):
        print("RC: online")
        self.running = True
        commands = []
        while self.running:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                continue
            except Exception as E:
                print("RCRECEIVER: caught exception:", str(E))
                continue

            data = data.decode("utf-8").split(";")
            commands.extend(data)
            if len(commands) >= 10:
                print("".join(commands))
                commands = []

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
        print("TCPSTREAMER: online")

    def connect(self, IP):
        super(TCPStreamer, self)._connectbase(IP, STREAM_SERVER_PORT, None)
        print("TCPSTREAMER: connected to {}:{}".format(IP, STREAM_SERVER_PORT))

    @property
    def frameshape(self):
        return str(self._frameshape)[1:-1].replace(", ", "x")

    def _determine_frame_shape(self):
        self.eye.open()
        success, frame = self.eye.read()
        if not success:
            success, frame = self._fall_back_to_white_noise_stream()
        self._frameshape = frame.shape
        self.eye.close()

    def _fall_back_to_white_noise_stream(self):
        print("TCPSTREAMER: Capture device unreachable, falling back to white noise stream!")
        self.eye = CaptureDevice(CaptureDeviceMocker)
        return self.eye.read()

    def run(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        pushed = 0
        self.eye.open()
        self.running = True
        for success, frame in self.eye.stream():
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype(DTYPE).tostring()  #
            ##########################################
            self.sock.sendall(serial)
            pushed += 1
            print("Pushed {:>3} frames".format(pushed))
            if not self.running:
                break
            time.sleep(1. / FPS)
        self.eye.close()
        print("TCPStreamer: socket and worker deleted! Exiting...")
