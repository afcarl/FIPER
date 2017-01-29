from __future__ import print_function

import time

import cv2

from FIPER.generic import *

print("OpenCV version:", cv2.__version__)


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

    def __init__(self, ID, address=None):
        self.ID = ID
        # self.eye = cv2.VideoCapture(0)
        self.eye = CaptureDeviceMocker
        self.rpm = 0
        self.msocket = None  # 4 message tranfer
        self.server_ip = None  # if UPD is used for data transfer

        # Try to infer the local IP address
        if address is None:
            address = my_ip()
        self.address = address

        self.dsocket = socket.socket(socket.AF_INET, DPROTOCOL)

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def connect(self, server_ip):
        """Establishes connections with the server"""

        # Read a single frame to infer the frame shape
        success, frame = self.eye.read()
        if not success:
            # If read fails, we assume no capture device is connected
            # and fall back to white noise streaming
            self.eye = CaptureDeviceMocker
            frame = self.eye.read()[1]

        # Initiate connection by setting up the message-passing
        # socket, then send ID and video frame shape to the server
        self.msocket = socket.socket(socket.AF_INET, MPROTOCOL)
        self.msocket.connect((server_ip, MESSAGEPORT))
        self.out("MSOCKET connected to {}:{}".format(server_ip, MESSAGEPORT))
        self.message(str(self.ID).encode(), t=0.5)
        self.message(str(frame.shape)[1:-1].replace(", ", "x").encode())

    def see(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        while 1:
            success, frame = self.eye.read()
            serial = frame.astype(DTYPE).tobytes()
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.dsocket.sendto(slc, (self.server_ip, STREAMPORT))
            self.out("Pushed array of shape: ", frame.shape)

    def message(self, m, t=0.):
        """Sends a bytes message through the message port"""
        for slc in (m[i:i + 1024] for i in range(0, len(m), 1024)):
            self.msocket.send(slc)
        self.msocket.send(b"ROGER")
        time.sleep(t)


if __name__ == '__main__':
    lightning_mcqueen = Car(ID=95, address=NOTE)
    lightning_mcqueen.connect(ip)
    lightning_mcqueen.see()
