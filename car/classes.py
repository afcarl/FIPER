from __future__ import print_function, absolute_import, division, unicode_literals

# STDLIB imports
import os
import time
import socket
import warnings
import threading as thr

# 3rd party imports
import cv2

# Project imports
from FIPER.generic import *

print("OpenCV version:", cv2.__version__)

DUMMY_VIDEOFILE = "/data/Prog/data/raw/vid/go.avi"
DUMMY_FRAMESIZE = (640, 480, 3)  # = 921,600 B in uint8


class CaptureDeviceMocker(object):
    """Mocks the interface of cv2.VideoCapture"""

    @staticmethod
    def read():
        """
        Mocks the functionality of VideoCapture().read():

        returns success code and a white noise frame
        """
        return True, white_noise(DUMMY_FRAMESIZE)


class TCPStreamer:

    def __init__(self, master, sock):
        self.master = master
        if not DUMMY_VIDEOFILE:
            self.eye = cv2.VideoCapture(0)
        elif not os.path.exists(DUMMY_VIDEOFILE):
            self.eye = CaptureDeviceMocker
        else:
            self.eye = cv2.VideoCapture(DUMMY_VIDEOFILE)

        success, frame = self.eye.read()
        if not success:
            warnings.warn("Capture device unreachable, falling back to white noise stream!",
                          RuntimeWarning)
            self.eye = CaptureDeviceMocker
            success, frame = self.eye.read()
        self.frameshape = frame.shape

        self.sock = sock
        self.worker = None

    def start(self):
        self.worker = thr.Thread(target=self.run, name="Streamer")
        self.worker.start()

    def frame(self):
        return self.eye.read()

    def run(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        pushed = 0
        while self.master.streaming:
            success, frame = self.frame()
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype(DTYPE).tostring()  #
            ##########################################
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.sock.send(slc)
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")
        print("Stream terminated!")
        self.worker = None


class CarBase(object):

    """
    A video stream server, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing
    """

    entity_type = "car"

    def __init__(self, ID, address):
        self.ID = ID

        self.messenger = None  # message channel wrapper
        self.send_message = None

        self.address = address

        self.live = True
        self.streaming = False

        self.stream_worker = None

    def connect(self, server_ip):
        """Establishes connections with the server"""

        try:
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            dsocket.bind((self.address, STREAM_SERVER_PORT))
            msocket.connect((server_ip, MESSAGE_SERVER_PORT))
            dsocket.listen(1)
        except:
            raise
        finally:
            self.shutdown()

        self.messenger = Messaging(msocket, tag=b"{}-{}:".format(self.entity_type, self.ID))

        introduction = "HELLO;" + str(self.streamer)[1:-1].replace(", ", "x")
        self.messenger.send(introduction.encode())

        dsocket, (ip, port) = dsocket.accept()
        self.streamer = TCPStreamer(self, dsocket)

        if ip != server_ip:
            warnings.warn("Received data connection from an unknown IP: {}:{}"
                          .format(ip, port))

    def launch_stream(self):
        """
        Launches the worker thread which streams video to the server
        Thread creation is done here too, because threads cannot be
        restarted.
        (Turning streaming off, then on again wouldn't be possible)
        """
        self.streaming = True
        self.stream_worker = thr.Thread(target=self.see)
        self.stream_worker.start()

    def terminate_stream(self):
        """Tears down the streaming thread"""
        self.streaming = False
        time.sleep(3)  # Wait for loop termination

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def shutdown(self):
        if self.streaming:
            self.terminate_stream()
        self.live = False

        self.dsocket.close()
        self.messenger.send("{} offline".format(self.ID))
        self.messenger.running = False

    def mainloop(self):
        """
        This loop wathces the messaging system and receives
        control commands from the server.
        """
        while self.live:
            msg = self.messenger.recv(timeout=1)
            if msg is None:
                continue
            self.out("Received message:", msg)
            if msg == "shutdown":
                self.shutdown()
                break
            elif msg == "stream on":
                if self.streaming:
                    self.out("Received <stream on>, when already streaming!")
                else:
                    self.launch_stream()
            elif msg == "stream off":
                self.terminate_stream()
            else:
                self.out("Received unknown command:", msg)
        self.out("Shutting down...")


class CarTCP(CarBase):

    """
    A video stream server, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing
    """

    def connect(self, server_ip):
        """Establishes connections with the server"""

        super(CarTCP, self).connect(server_ip)

        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dsocket.bind((self.address, STREAM_SERVER_PORT))
        self.dsocket.listen(1)
        self.dsocket, addr = self.dsocket.accept()
        if addr != server_ip:
            warnings.warn("Received data connection from an unknown IP:", addr)


class CarUDP(CarBase):

    """
    A video stream server, located somewhere on the local network.
    It has a mounted video capture device, read by openCV.
    Video frames are forwarded to a central server for further processing
    """

    def connect(self, server_ip):
        """Establishes connections with the server"""
        super(CarUDP, self).connect(server_ip)
        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def see(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        pushed = 0
        while self.streaming:
            success, frame = self.eye.read()
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype(DTYPE).tostring()  #
            ##########################################
            for slc in (serial[i:i+1024] for i in range(0, len(serial), 1024)):
                self.dsocket.send(slc)
            pushed += 1
            print("\rPushed {:>3} frames".format(pushed), end="")
        self.out("Stream terminated!")


def readargs():
    pleading = "Please supply "
    question = ["the local IP address of this Car",
                "the remote IP address for the server",
                "a unique ID for this Car"]
    return [raw_input(pleading + q + " > ") for q in question]


def main():
    import sys

    if len(sys.argv) == 4:
        localIP, serverIP, carID = sys.argv[1:4]
    else:
        localIP, serverIP, carID = readargs()

    lightning_mcqueen = CarTCP(ID=carID, address=localIP)
    try:
        lightning_mcqueen.connect(serverIP)
        lightning_mcqueen.mainloop()
    except Exception as E:
        print("Exception occured:", E.message)
    finally:
        lightning_mcqueen.shutdown()

    print("OUTSIDE: Car was shut down nicely.")


if __name__ == '__main__':
    main()
