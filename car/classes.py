from __future__ import print_function

import time

import cv2

from FIPER.generic import *

print("OpenCV version:", cv2.__version__)


DELTA = 2.
XMAX = 100.
YMAX = 100.


class CaptureDeviceMocker(object):
    """Mocks the interface of cv2.VideoCapture"""

    @staticmethod
    def read():
        """
        Mocks the functionality of VideoCapture().read():

        returns success code and a white noise frame
        """
        return True, white_noise(DUMMY_FRAMESIZE)


class Car(object):

    """
    A video stream server, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing
    """

    def __init__(self, ID):
        self.ID = ID
        # self.eye = cv2.VideoCapture(0)
        self.eye = CaptureDeviceMocker
        self.rpm = 0
        self.msocket = None  # 4 message tranfer

        # Infer the local IP address
        tmpsck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmpsck.connect(("8.8.8.8", 80))
        self.address = tmpsck.getsockname()[0]
        tmpsck.close()

        self.dsocket = socket.socket(socket.AF_INET, DPROTOCOL)
        self.dsocket.bind((self.address, STREAMPORT))

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def connect(self, server_ip):
        """Establishes connections with the server"""

        success, frame = self.eye.read()
        if not success:
            self.eye = CaptureDeviceMocker
            frame = self.eye.read()[1]

        # Initiate connection by setting up the message-passing
        # socket, then send ID and video frame shape to the server
        self.msocket = socket.socket(socket.AF_INET, MPROTOCOL)
        self.msocket.connect((server_ip, MESSAGEPORT))
        self.out("MSOCKET connected to {}:{}".format(server_ip, MESSAGEPORT))
        self.message(str(self.ID).encode(), t=0.5)
        self.message(str(frame.shape)[1:-1].replace(", ", "x").encode())

        # Set up the stream socket and complete the connection
        self.out("Waiting for UDP connection...")
        self.dsocket.listen(1)
        self.dsocket, dadr = self.dsocket.accept()
        self.out("DSOCKET connected to {}:{}".format(dadr[0], STREAMPORT))
        # assert dadr[0] == server_ip

    def see(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        while 1:
            success, frame = self.eye.read()
            serial = frame.astype(DTYPE).tobytes()
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.dsocket.send(slc)
            self.out("Pushed array of shape: ", frame.shape)

    def message(self, m, t=0.):
        """Sends a bytes message through the message port"""
        slices = (m[start:start+1024] for start in range(0, len(m), 1024))
        for slc in slices:
            self.msocket.send(slc)
        self.msocket.send(b"ROGER")
        time.sleep(t)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "192.168.1.2"

    lightning_mcqueen = Car(ID=95)
    lightning_mcqueen.connect(ip)
    lightning_mcqueen.see()
