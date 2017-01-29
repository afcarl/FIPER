from __future__ import print_function

import time
import threading as thr
import socket as sck

import cv2

from FIPER.generic import *


class CarInterface(object):
    """
    Implemented as a video stream CLIENT
    """

    def __init__(self, msock, srvip):
        # The server's message socket
        self.msocket = msock

        # car_ID and framesize are sent throught the message socket
        self.car_ID = self.get_message()
        self.framesize = [int(s) for s in self.get_message().split("x")]
        self.out("Target ID:", self.car_ID)
        self.out("Framesize:", self.framesize)

        self.dsocket = sck.socket(sck.AF_INET, DPROTOCOL)
        self.dsocket.bind((srvip, STREAMPORT))
        self.out("Stream receiver port bound to {}:{}".format(srvip, STREAMPORT))

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("IFACE {}: ".format(self.car_ID), *args, sep=sep, end=end)

    def get_message(self):
        """Receive a message from the message port"""
        data = b""
        while data[-5:] != b"ROGER":
            data += self.msocket.recv(1024)
        return data[:-5].decode("utf8")

    def get_stream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            data = data[datalen:]

    def display_stream(self):
        for i, pic in enumerate(self.get_stream(), start=1):
            self.out("\rRecieved {:>3} frames of shape {}"
                     .format(i, pic.shape), end="")
            cv2.imshow("Stream", pic)
            cv2.waitKey(1)
        print()

    def __repr__(self):
        return "CarInterface {}".format(self.car_ID)


class FleetHandler(object):
    """
    Handles a Fleet of Cars
    """

    def __init__(self, ip=None):
        self.ip = ip
        self.cars = []
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.bind(((ip if ip is not None else my_ip()), MESSAGEPORT))
        print("SERVER: msocket bound to", ip)

        self.listener = thr.Thread(name="Listener", target=self.listen)
        self.watcher = thr.Thread(name="Watcher", target=self.watch)

    def start_listening(self):
        self.listener.start()
        # self.listen()

    def start_watching(self):
        self.watcher.start()

    def listen(self):
        """
        Accepts connections from cars
        self.listener runs this in a separate thread
        """
        print("SERVER: Awaiting connections...")
        while 1:
            self.msocket.listen(1)
            conn, address = self.msocket.accept()
            print("SERVER: Received connection from", address)
            self.cars.append(CarInterface(conn, self.ip))

    def watch(self):
        """
        Displays video streams from CarInterfaces.
        self.watcher runs this in a separate thread.
        """
        while 1:
            while not self.cars:
                time.sleep(3)
            car = self.cars[0]
            print("SERVER: Watching Car:", car.car_ID)
            car.display_stream()


def main():
    """Does the argparse and launches a server"""
    import sys

    if len(sys.argv) < 2:
        raise RuntimeError("Please supply the server's IP address as the first argument!")

    server = FleetHandler(sys.argv[1])
    server.start_listening()
    server.start_watching()
    while 1:
        time.sleep(20)
        print("OUTSIDE: Cars online:", len(server.cars))

# TODO: this is a bad approach.
# This setup isn't able to handle multiple car objects,
# because it will try to bind the same ip:port combo for
# every CarInterface.
# Maybe every interface should have an own UDP port for
# receiving the video stream from the car.
# But cars send their streams to a specified address, so
# the UDP port bound for a car should be broadcasted or
# sent to it via the message port.

if __name__ == '__main__':
    main()
