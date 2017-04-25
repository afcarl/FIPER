from __future__ import print_function, absolute_import, unicode_literals

# stdlib imports
import os
import abc
import time
import socket
import warnings
import threading as thr

# 3rd party imports
import cv2

# project imports
from FIPER.generic.util import CaptureDeviceMocker
from FIPER.generic.const import DTYPE, CAR_PROBE_PORT
from FIPER.generic.abstract import AbstractConsole


class ChannelBase(object):

    __metaclass__ = abc.ABCMeta

    type = ""

    def __init__(self):
        self.sock = None
        self.running = False
        self.worker = None

    def connect(self, IP, port):
        self.sock = socket.create_connection((IP, port), timeout=1)

    def start(self):
        if self.sock is None:
            print("{}: object unitialized! Please call connect(sock) first!"
                  .format(self.type))
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


class RCReceiver(ChannelBase):

    """
    Handles the RC command receiving.
    Runs in separate thread, started in TCPCar._connect()
    """

    type = "RCReceiver"

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
        self.cleanup()
        print("TCPStreamer: socket and worker deleted! Exiting...")


class Idle(object):

    """
    Cars enter this state initially, if no server IP is given for them.
    In the Idle state, they can be probed and if the probing message is
    valid, they send back their CarID and IP address to the probe.
    """

    def __init__(self, myIP, myID):
        self.IP = myIP
        self.ID = myID
        self.sock = None
        self.conn = None
        self.remote_address = None

    def _setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.bind((self.IP, CAR_PROBE_PORT))
        self.sock.listen(1)
        print("IDLE: Awaiting connection... Hit Ctrl-C to break!".format(self.ID))

    def _read_message_from_probe(self):
        try:
            m = self.conn.recv(1024).decode("utf-8")
        except socket.timeout:
            return
        else:
            return m if m in ("probing", "connect") else None

    def _new_connection_causes_loopbreak(self):
        msg = self._read_message_from_probe()
        if msg is None:
            print("IDLE: empty message from", self.remote_address[0])
            return False

        print("IDLE: probed by: {}; msg: {}".format(self.IP, msg))
        self._respond_to_probe(msg)
        return msg == "connect"

    def _respond_to_probe(self, msg):
        m = "car-{} @ {}".format(self.ID, self.IP)
        if msg in ("connect", "probing"):
            self.conn.send(m.encode())
        else:
            print("IDLE: invalid message received! Ignoring...")

    def mainloop(self):
        self._setup_socket()
        while 1:
            try:
                self.conn, self.remote_address = self.sock.accept()
            except socket.timeout:
                pass
            else:
                if self._new_connection_causes_loopbreak():
                    break
                self.conn.close()
                self.conn = None
        return self.remote_address[0]


class Eye(object):

    """
    Methods used for setting up a video capture device.
    """

    # noinspection PyArgumentList
    def __init__(self, dev=None, dummyfile=None):
        if dev is None:
            if not dummyfile:
                self.device = lambda: cv2.VideoCapture(0)
            elif not os.path.exists(dummyfile):
                self.device = CaptureDeviceMocker
            else:
                self.device = lambda: cv2.VideoCapture(dummyfile)
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


class Ear(AbstractConsole):

    def __init__(self, messenger, **commands):
        super(Ear, self).__init__("Car", commands_dict=commands)
        self.messenger = messenger
        print("EAR: online!")

    def read_cmd(self):
        m = self.messenger.recv(timeout=1)
        if m is None:
            return
        return m


class Handshake(object):

    """
    Coordinates the probing protocol's
    handshake process on the car's side
    """

    @staticmethod
    def perform(streamer, messenger):
        Handshake._send_introduction(streamer, messenger)
        hello = Handshake._read_response(messenger)
        if not Handshake._validate_response(hello):
            return None
        return hello

    @staticmethod
    def _send_introduction(streamer, messenger):
        introduction = "HELLO;" + streamer.frameshape
        for i in range(3):
            print("HANDSHAKE: Sending introduction:", introduction)
            messenger.send(introduction.encode())
            time.sleep(0.5)

    @staticmethod
    def _read_response(messenger):
        for i in range(4, -1, -1):
            hello = messenger.recv(timeout=1)
            if hello is not None:
                return hello

    @staticmethod
    def _validate_response(hello):
        return hello == "HELLO"
