import socket
import time

import numpy as np

import cv2

print "OpenCV version:", cv2.__version__

DUMMY_FRAMESIZE = (640, 480)
DELTA = 2.
XMAX = 100
YMAX = 100


class Car:

    """
    Class for reference
    """

    def __init__(self, ID, sock=None):
        self.ID = ID
        self.eye = None
        self.socket = sock if sock is not None else self.connect()
        self.position = np.array([1., 0.])  # XY coords
        self.velocity = np.array([0., 0.])  # as vector

    def connect(self, address=None, port=1234):
        if address is None:
            address = "127.0.0.1"

        # socket is set to datagram (UDP) at the moment.
        sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sck.bind((address, port))
        print "CAR {} BOUND TO {}:{}".format(self.ID, address, port)
        return sck

    def dummy_move(self):
        """
        Modify velocity by a random gradient.

        Clumsy, why would I modify the gradient at every timestep?
        """
        nabla = np.random.uniform(-DELTA, DELTA, (2,))
        self.velocity += nabla
        self.position += self.velocity
        if self.position[0] > XMAX:
            self.position[0] = XMAX
            self.velocity[0] = 0
        if self.position[0] < 0:
            self.position[0] = 0
            self.velocity[0] = 0
        if self.position[1] > YMAX:
            self.position[1] = YMAX
            self.velocity[1] = 0
        if self.position[1] < 0:
            self.position[1] = 0
            self.velocity[1] = 0

    def cv_see(self):
        """Obtain frames from the capture device via openCV"""
        if self.eye is None:
            self.eye = cv2.VideoCapture(0)  # device ID goes here
        # Do we do any image preprocessing on the car?
        bframe = self.eye.read().tobytes() + b"\0"
        self.push_frame(bframe)

    def dummy_see(self):
        """Obtain a white noise frame"""
        bframe = np.random.randn(*DUMMY_FRAMESIZE).tobytes() + b"\0"
        self.push_frame(bframe)

    def push_frame(self, bframe):
        """
        Push a frame through the socket

        :param bframe: binarized numpy array
        :return:
        """
        for slc in (bframe[start:start+1024] for start in range(0, len(bframe), 1024)):
            self.socket.sendall(slc)
        self.socket.sendall(b"\0")

    def emulate(self, display=None):
        sleep = 0.1
        if display is not None:
            obj = display.plot(self.position[0], self.position[1], "o", color="black")[0]
            ax = display.gca()
            ax.set_xlim(0, XMAX)
            ax.set_ylim(0, YMAX)
        while 1:
            self.dummy_move()
            print "I am at ({:>6.2f}, {:>6.2f}), v = {v:>5.2f}".format(
                *self.position, v=abs(self.velocity.sum()))
            # self.send_frame()
            if display is not None:
                x, y = self.position
                obj.set_xdata(x)
                obj.set_ydata(y)
                display.pause(sleep)
            else:
                time.sleep(sleep)

if __name__ == '__main__':
    from matplotlib import pyplot as plt
    plt.ion()

    lightning_mcqueen = Car(ID=95)

    lightning_mcqueen.emulate(display=plt)
