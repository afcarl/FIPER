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

    def __init__(self, msock, address):
        self.msocket = msock
        self.address = address
        
        self.car_ID = self.get_message()
        self.framesize = self.get_message().split("x")
        self.out("Target ID:", self.car_ID)
        self.out("Framesize:", self.framesize)

        self.dsocket = sck.socket(sck.AF_INET, DPROTOCOL)
        self.dsocket.connect((address[0], STREAMPORT))
        self.out("Successful data connection to {}:{}".format(address[0], STREAMPORT))

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("IFACE {}: ".format(self.car_ID), *args, sep=sep, end=end)

    def get_message(self):
        data = b""
        while data[-5:] != b"ROGER":
            data += self.msocket.recv(1024)
        return data[:-5]

    def get_stream(self):
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            data = data[datalen:]

    def display_stream(self):
        for pic in self.get_stream():
            self.out("Recieved frame of shape", pic.shape)
            cv2.imshow("Stream", pic)

    def __repr__(self):
        return "CarInterface {} @ {}".format(self.car_ID, self.address)


class FleetHandler(object):
    """
    Handles a Fleet of Cars
    """

    def __init__(self, ip=None):
        self.cars = []
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.bind(((ip if ip is not None else my_ip()), MESSAGEPORT))
        print("SERVER: msocket bound to", ip)

        self.listener = thr.Thread(name="Listener", target=self.listen)
        self.watcher = thr.Thread(name="Listener", target=self.watch)

    def start_listening(self):
        self.listener.start()
        # self.listen()

    def start_watching(self):
        self.watcher.start()

    def listen(self):
        print("SERVER: Awaiting connections...")
        while 1:
            self.msocket.listen(1)
            conn, address = self.msocket.accept()
            print("SERVER: Received connection from", address)
            self.cars.append(CarInterface(conn, address))

    def watch(self):
        while 1:
            while not self.cars:
                time.sleep(3)
            car = self.cars[0]
            print("SERVER: Watching Car:", car.car_ID)
            car.display_stream()

if __name__ == '__main__':
    server = FleetHandler("192.168.1.5")
    server.start_listening()
    server.start_watching()
    while 1:
        time.sleep(3)
        print("OUTSIDE: Cars online:", len(server.cars))
