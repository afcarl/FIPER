from __future__ import print_function

import time
import socket

import numpy as np
import cv2

from minimalgeneric import configparse


def getsrv(ip, port, timeout=0):
    s = socket.socket()
    while 1:
        try:
            s.bind((ip, port))
            break
        except socket.error as E:
            if E.errno == 98:
                print("Socket not available yet... Waiting...")
                time.sleep(1)
            else:
                raise
    s.listen(1)
    if timeout:
        s.settimeout(timeout)
    return s


def listen(cfg):
    print("Awaiting connection...")
    mserver = getsrv(cfg["client_ip"], cfg["message_port"], timeout=1)
    dserver = getsrv(cfg["client_ip"], cfg["stream_port"])

    while 1:
        try:
            mconn, addr = mserver.accept()
            print("Connection from", addr)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("Exiting...")
            return
        except Exception as E:
            print("Caught exception:", str(E))
            return
        else:
            dconn, addr = dserver.accept()
            break
    return mconn, dconn


def framestream(dconn, cfg):
    datalen = np.prod(cfg["webcam_resolution"])
    data = b""
    while 1:
        while len(data) < datalen:
            data += dconn.recv(1024)
        yield np.fromstring(data[:datalen], dtype="uint8").reshape(cfg["webcam_resolution"])
        data = data[datalen:]


def display(mconn, dconn, cfg):
    print("Displaying framestream...")
    for frame in framestream(dconn, cfg):
        cv2.imshow("OpenCV", frame)
        key = cv2.waitKey(30)
        if key >= 0:
            mconn.send(str(key))
        if key == 27:
            cv2.destroyAllWindows()
            break


if __name__ == '__main__':
    config = configparse()
    mc, dc = listen(config)
    display(mc, dc, config)
