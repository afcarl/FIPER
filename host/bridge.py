import socket as sck

import numpy as np

from FIPER.generic import FRAMESIZE, STREAMPORT


class CarInterface:
    """
    Implemented as a video stream CLIENT
    """

    def __init__(self, address):
        self.connection = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        self.connection.connect((address, 1234))

    def get_stream(self):
        data = []
        slc = b" "
        while slc[-1] != b"\0":
            slc = self.connection.recv(1024)
            data.append(slc)
        raise RuntimeError("Sorry, under construction")
        data.append(slc[:-1])

        frame = np.fromstring(b"".join(data)).reshape(640, 480, 3)
        yield frame


if __name__ == '__main__':
    from sys import argv

    if len(argv) > 1:
        ip = argv[1]
    else:
        ip = "127.0.0.1"

    ifc = CarInterface(ip)
    for pic in ifc.get_stream():
        print "RECVD pic OF SHAPE", pic.shape
