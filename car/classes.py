from __future__ import print_function

# STDLIB imports
import time
import warnings

# 3rd party imports
import cv2

# Project imports
from FIPER.generic import *

print("OpenCV version:", cv2.__version__)


class CaptureDeviceMockerWhite(object):
    """Mocks the interface of cv2.VideoCapture"""

    @staticmethod
    def read():
        """
        Mocks the functionality of VideoCapture().read():

        returns success code and a white noise frame
        """
        return True, white_noise(DUMMY_FRAMESIZE)


class CaptureDeviceMockerFile(object):
    """Mocks the interface of cv2.VideoCapture"""

    myreader = cv2.VideoCapture(DUMMY_VIDEOFILE)

    @staticmethod
    def read():
        """
        Mocks the functionality of VideoCapture().read():

        reads a file frame-by-frame
        """
        return CaptureDeviceMockerFile.myreader.read()


class Car(object):

    """
    A video stream server, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing
    """

    def __init__(self, ID, address):
        self.ID = ID

        if not DUMMY_VIDEOFILE:
            self.eye = cv2.VideoCapture(0)
        else:
            self.eye = CaptureDeviceMockerFile

        self.msocket = None  # message transfer socket
        self.server_ip = None  # this will be the UDP stream's target

        # Try to infer the local IP address
        self.address = address

        self.dsocket = socket.socket(socket.AF_INET, DPROTOCOL)

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def connect(self, server_ip):
        """Establishes connections with the server"""

        self.server_ip = server_ip

        # Read a single frame to infer the frame shape
        success, frame = self.eye.read()
        if not success:
            self.eye = CaptureDeviceMockerWhite
            frame = self.eye.read()[1]
            msg = "Capture device unreachable!\n"
            msg += "Falling back to white noise stream!"
            warnings.warn(msg)

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
        pushed = 0
        while 1:
            success, frame = self.eye.read()
            serial = frame.astype(DTYPE).tostring()
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.dsocket.sendto(slc, (self.server_ip, STREAMPORT))
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")

    def message(self, m, t=0.):
        """Sends a bytes message through the message port"""
        for slc in (m[i:i + 1024] for i in range(0, len(m), 1024)):
            self.msocket.send(slc)
        self.msocket.send(b"ROGER")
        time.sleep(t)


def main():
    import sys

    if len(sys.argv) < 3:
        msg = "Please supply the local IP address of this\n" \
              + "car as the first argument and the server's\n" \
              + "IP address as the second argument!"
        raise RuntimeError(msg)
    lightning_mcqueen = Car(ID=95, address=sys.argv[1])
    lightning_mcqueen.connect(sys.argv[2])
    lightning_mcqueen.see()


if __name__ == '__main__':
    main()
