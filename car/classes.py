from __future__ import print_function

import time
import pickle
import socket

import numpy as np

import cv2

from FIPER.generic import FRAMESIZE, STREAMPORT, TICK

print("OpenCV version:", cv2.__version__)


DELTA = 2.
XMAX = 100.
YMAX = 100.


class Car:

    """
    Implemented as a video stream SERVER
    """

    def __init__(self, ID, address=None):
        self.ID = ID
        self.eye = None
        self.address = address  # Should we NOT use a default port number?
        self.socket = None
        self.position = np.array([XMAX, YMAX]) / 2  # XY coords
        self.velocity = np.array([0., 0.])  # as vector
        self.rpm = 0
        self.connect()

    def out(self, *args, **kw):
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("CAR {}: ".format(self.ID), *args, sep=sep, end=end)

    def connect(self):
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 'tis UDP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 'tis TCP
        self.socket.bind((self.address, STREAMPORT))
        self.out("BOUND TO {}:{}".format(self.address, STREAMPORT))
        self.out("Awaiting connection...")
        self.socket.listen(1)
        self.socket, adr = self.socket.accept()
        self.out("Connection from", adr)

    def dummy_move(self):
        """
        This method is REALLY unnecessary.
        """
        nabla = np.random.uniform(-DELTA, DELTA, (2,))  # acceleration
        self.velocity += nabla
        self.position += self.velocity
        if self.position[0] > XMAX:
            self.position[0] = XMAX
            self.velocity[0] = -self.velocity[0] * 0.25  # ricochet
        if self.position[0] < 0:
            self.position[0] = 0
            self.velocity[0] = -self.velocity[0] * 0.25
        if self.position[1] > YMAX:
            self.position[1] = YMAX
            self.velocity[1] = -self.velocity[1] * 0.25
        if self.position[1] < 0:
            self.position[1] = 0
            self.velocity[1] = -self.velocity[1] * 0.25

        # I'm having so much fun with this :D
        self.velocity *= 0.90  # friction

    def cv_see(self):
        """Obtain frames from the capture device via openCV"""
        if self.eye is None:
            self.eye = cv2.VideoCapture(0)  # device ID goes here
        # Do we do any image preprocessing on the car?
        while 1:
            self.push_frame(self.eye.read().astype(int))

    def dummy_see(self):
        """Obtain a white noise frame"""
        self.out("Starting white noise stream...".format(self.ID))
        while 1:
            frame = (np.random.randn(*FRAMESIZE) * 255).astype(int)
            self.push_frame(frame)

    def push_frame(self, ndarray):
        """
        Push a frame through the socket

        :param ndarray: 3d numpy array of dtype: int
        :return:
        """
        serial = pickle.dumps(ndarray, protocol=0)
        slices = (serial[start:start + 1024] for start in
                  range(0, len(serial), 1024))
        for slc in slices:
            self.socket.send(slc)
        self.out("Pushed array of shape", ndarray.shape)

    def emulate(self, display=True):
        if display:
            from matplotlib import pyplot as plt
            plt.ion()
            obj = plt.plot(self.position[0], self.position[1], "o", color="black")[0]
            ax = plt.gca()
            ax.set_xlim(0, XMAX)
            ax.set_ylim(0, YMAX)
        while 1:
            # self.dummy_move()
            # self.out("I am at ({:>6.2f}, {:>6.2f}), v = {v:>5.2f}".format(
            #     *self.position, v=abs(self.velocity.sum())))
            self.dummy_see()
            if display:
                x, y = self.position
                obj.set_xdata(x)
                obj.set_ydata(y)
                plt.pause(TICK)
            else:
                time.sleep(TICK)

if __name__ == '__main__':
    lightning_mcqueen = Car(ID=95, address="127.0.0.1")
    lightning_mcqueen.emulate(display=False)
