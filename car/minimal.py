from __future__ import print_function, unicode_literals, absolute_import

import sys
import time
import socket
import threading

import cv2

vdev = cv2.VideoCapture(0)


def connect():
    ip = sys.argv[-1] if len(sys.argv) == 2 else "127.0.0.1"
    print("Establishing connection...")
    while 1:
        try:
            msock = socket.create_connection((ip, 1234))
        except KeyboardInterrupt:
            print("Exiting...")
            return None
        except Exception as E:
            print("Caught:", str(E))
            time.sleep(1)
        else:
            dsock = socket.create_connection((ip, 1235))
            return msock, dsock


def command_inflow(msock):
    time.sleep(1)
    print("Command job launched...")
    while 1:
        msg = msock.recv(1024)
        print(msg)


def stream(dsock):
    print("Starting stream...")
    while 1:
        success, frame = vdev.read()
        frame = frame.astype("uint8").ravel()
        dsock.sendall(frame.tostring())
        time.sleep(1/30)


def main():
    msock, dsock = connect()
    command_job = threading.Thread(target=command_inflow, args=(msock,), name="Command Job")
    command_job.start()
    stream(dsock)


if __name__ == '__main__':
    main()
