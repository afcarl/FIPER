import socket
import time

import numpy as np


DUMMY_FRAMESIZE = (640, 480)
DELTA = 2.
XMAX = 100
YMAX = 100


class Car:

    """
    A dummy class for reference

    Normally cars will just exist somewhere on the network
    """

    def __init__(self, ID, sock=None):
        self.ID = ID
        self.socket = sock if sock is not None else self.connect()
        self.position = np.array([1., 0.])  # XY coords
        self.velocity = np.array([0., 0.])  # as vector

    def connect(self, address=None, port=1234):
        if address is None:
            address = "127.0.0.1"
        sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sck.bind((address, port))
        print "CAR {} BOUND TO {}:{}".format(self.ID, address, port)
        return sck

    def move_around(self):
        delta = np.random.uniform(-DELTA, DELTA, (2,))
        self.velocity += delta
        self.position += self.velocity
        if self.position[0] > XMAX:
            self.position[0] = XMAX
            self.velocity[0] = 0
        if self.position[0] < 0:
            self.position[0] = 0
            self.velocity = 0
        if self.position[1] > YMAX:
            self.position[1] = YMAX
            self.velocity[1] = 0
        if self.position[1] < 0:
            self.position[1] = 0
            self.velocity[1] = 0

    def send_frame(self):
        bframe = np.random.randn(*DUMMY_FRAMESIZE).tobytes()
        for slc in (bframe[start:start+1024] for start in range(0, len(bframe), 1024)):
            self.socket.sendall(slc)
        self.socket.sendall("\0")

    def emulate(self, display=False):
        if display:
            from matplotlib import pyplot as plt
            plt.ion()
            lines = plt.plot(self.position[0], self.position[1], "o", color="black")[0]
            ax = plt.gca()
            ax.set_xlim(0, XMAX)
            ax.set_ylim(0, YMAX)
            plt.show()
        while 1:
            self.move_around()
            print "I am at ({:>5.2f}, {:>5.2f})".format(*self.position)
            # self.send_frame()
            if display:
                x, y = self.position
                lines.set_xdata(x)
                lines.set_ydata(y)

            time.sleep(1)

if __name__ == '__main__':
    lightning_mcqueen = Car(ID=95)
    lightning_mcqueen.emulate(display=False)


