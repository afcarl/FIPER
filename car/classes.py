from __future__ import print_function, absolute_import, unicode_literals

# STDLIB imports
import os
import time
import socket
import warnings
import threading as thr

# 3rd party imports
import cv2

# Project imports
import sys
from FIPER.generic import Messaging
from FIPER.generic import DTYPE, MESSAGE_SERVER_PORT, STREAM_SERVER_PORT
from FIPER.generic import CaptureDeviceMocker

DUMMY_VIDEOFILE = ""


class TCPStreamer(object):

    """
    Abstraction of the video streamer.
    Factored out from TCPCar, this class enables
    switching the stream on and off in a managed way.
    """

    def __init__(self, master):
        self.master = master
        self.sock = None
        self.eye = None
        self._frameshape = None

        self._setup_capture_device()
        self._determine_frame_shape()

        self.running = False
        self.worker = None

    def connect(self, sock):
        self.sock = sock

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

    def start(self):
        if self.sock is None:
            print("TCPStreamer: object unitialized! Please call setup(dsock) first!")
            return
        if not self.running:
            self.worker = thr.Thread(target=self.run, name="Streamer")
            self.worker.start()

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
        print("CAR STREAMER: Stream terminated!")
        self.worker = None


class TCPCar(object):

    """
    A video streamer, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing.
    The TCPCar is implemented as a TCP client.
    """

    entity_type = "car"

    def __init__(self, ID, address, server_ip):
        self.ID = ID
        self.address = address

        self.messenger = None  # type: Messaging
        self.streamer = None  # type: TCPStreamer
        self.live = False

        self.connect(server_ip)

    def connect(self, server_ip):
        """Establishes connections with the server"""

        self.streamer = TCPStreamer(self)

        def setup_message_connection():
            msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msocket.connect((server_ip, MESSAGE_SERVER_PORT))
            self.messenger = Messaging(msocket, tag=b"{}-{}:".format(self.entity_type, self.ID))

        def setup_data_connection():
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.connect((server_ip, STREAM_SERVER_PORT))
            self.streamer.connect(dsocket)

        def perform_handshake():
            introduction = "HELLO;" + self.streamer.frameshape
            self.messenger.send(introduction.encode())
            hello = None
            while hello is None:
                hello = self.messenger.recv(timeout=1)
                self.out("Received handshake:", hello)
            if hello != "HELLO":
                print("Wrong handshake from server! Shutting down!")
                raise RuntimeError("Handshake error!")

        # Function body starts here {just to be clear :)}
        setup_message_connection()
        perform_handshake()
        setup_data_connection()

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get(b"sep", " "), kw.get(b"end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def shutdown(self, msg=None):
        if msg is not None:
            self.out(msg)
        if self.streamer is not None:
            self.streamer.running = False
        if self.messenger is not None:
            self.messenger.send("offline")
            time.sleep(1)
            self.messenger.teardown()
        self.live = False

    def mainloop(self):
        """
        This loop wathces the messaging system and receives
        control commands from the server.
        """
        self.live = True
        while self.live:
            msg = self.messenger.recv(timeout=1)
            if msg is None:
                continue
            self.out("Received message:", msg)
            if msg == "shutdown":
                self.shutdown()
                break
            elif msg == "stream on":
                self.streamer.start()
            elif msg == "stream off":
                self.streamer.running = False
            else:
                self.out("Received unknown command:", msg)
        self.out("Shutting down...")


def readargs():
    import sys
    if len(sys.argv) == 4:
        return sys.argv[1:4]

    pleading = "Please supply "
    question = ["the local IP address of this Car",
                "the remote IP address for the server",
                "a unique ID for this Car"]
    return [raw_input(pleading + q + " > ") for q in question]


def debugmain(ID):
    lightning_mcqueen = TCPCar(ID=ID, address="127.0.0.1", server_ip="127.0.0.1")
    lightning_mcqueen.mainloop()

    print("OUTSIDE: Car was shut down nicely.")


def main():
    localIP, serverIP, carID = readargs()
    lightning_mcqueen = TCPCar(ID=carID, address=localIP, server_ip=serverIP)
    lightning_mcqueen.mainloop()

    print("OUTSIDE: Car was shut down nicely.")


if __name__ == '__main__':
    debugmain("TestCar" if len(sys.argv) == 1 else sys.argv[1])
