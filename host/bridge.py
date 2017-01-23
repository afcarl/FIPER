from __future__ import print_function

import pickle
import socket as sck

import numpy as np

from FIPER.generic import FRAMESIZE, STREAMPORT, TICK


class CarInterface:
    """
    Implemented as a video stream CLIENT
    """

    def __init__(self, address):
        self.connection = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        self.connection.connect((address, STREAMPORT))
        print("IFACE: successful connection to {}:{}".format(address, STREAMPORT))

    def get_stream(self):
        data = b""
        while 1:
            d = self.connection.recv(1024)
            if d[:6] == b"cnumpy" and data:
                frame = pickle.loads(data)
                yield frame
                data = b""
            data += d


if __name__ == '__main__':
    from sys import argv
    from matplotlib import pyplot as plt

    if len(argv) > 1:
        ip = argv[1]
    else:
        ip = "127.0.0.1"

    plt.ion()
    obj = plt.imshow(np.zeros(FRAMESIZE).astype(int), vmin=0, vmax=255)
    ifc = CarInterface(ip)
    for pic in ifc.get_stream():
        print("RECVD pic OF SHAPE", pic.shape)
        obj.set_data(pic)
        plt.pause(TICK)
