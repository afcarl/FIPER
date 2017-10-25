from __future__ import print_function

import sys
import time
import socket
import threading

import numpy as np
import cv2


FPS = 15
RECEIVER_PORT = 1234
STREAM_PORT = 1235


class ChannelBase:
    port = -1

    def __init__(self, ip, timeout=0):
        self.running = False
        self.job = None
        self.sock = socket.create_connection((ip, self.port))
        if timeout:
            self.sock.settimeout(timeout)

    def start(self):
        if self.job is not None:
            return
        self.job = threading.Thread(target=self.mainloop)
        self.job.start()

    def mainloop(self):
        raise NotImplementedError

    def stop(self):
        self.running = False
        self.sock.close()


class Stream(ChannelBase):
    port = STREAM_PORT

    _dev = cv2.VideoCapture(0)

    if _dev.read()[0] is False:
        print("Falling back to white noise stream!")

        @staticmethod
        def readframe():
            return True, np.random.randn(480, 640, 3)
    else:
        def readframe(self):
            return self._dev.read()

    def mainloop(self):
        print("Starting stream...")
        self.running = True
        while self.running:
            success, frame = self.readframe()
            frame = frame.astype("uint8").ravel()
            self.sock.sendall(frame.tostring())
            time.sleep(1 / 30)


class Receiver(ChannelBase):
    port = RECEIVER_PORT

    def mainloop(self):
        tick = 1/FPS
        self.sock.settimeout(tick)
        self.running = True
        while self.running:
            print("Command job launched...")
            try:
                msg = self.sock.recv(1024)
            except socket.timeout:
                pass
            except Exception as E:
                print("Receiver caught:", str(E))
                self.running = False
            else:
                if not msg or msg == "27":
                    print("Received exit message!")
                    self.running = False
                time.sleep(tick)
        self.stop()


def connect():
    ip = sys.argv[-1] if len(sys.argv) == 2 else "127.0.0.1"
    print("Establishing connection...")
    while 1:
        try:
            rec = Receiver(ip)
        except KeyboardInterrupt:
            print("Exiting...")
            return None
        except Exception as E:
            print("Caught:", str(E))
            time.sleep(1)
        else:
            stream = Stream(ip)
            return rec, stream


def main():
    rec, strm = connect()
    rec.start()
    try:
        strm.mainloop()
    except Exception as E:
        print("Caught:", str(E))
        rec.stop()
        strm.stop()


if __name__ == '__main__':
    main()
