import socket as sck

import numpy as np

REMOTE = "127.0.0.1", 2345
LOCAL = "127.0.0.1", 1234


def generate_frames(address, port):
    sock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(1)

    conn, addr = sock.accept()
    print "Connection from {}".format(addr)

    while 1:
        data = b""
        while 1:
            d = conn.recv(1024)
            if d[-4:] == b"NULL":
                data += d[:-4]
                break
            data += d
        data = np.fromstring(data).reshape(640, 480, 3)
        yield data

if __name__ == '__main__':
    for array in generate_frames(*LOCAL):
        print "Got array of shape", array.shape
