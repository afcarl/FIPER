from __future__ import print_function, absolute_import, unicode_literals

import time
import socket
import threading as thr

import sys
from FIPER.generic.const import (
    CAR_PROBE_PORT,
)


class Echo(object):

    instances = 0

    def __init__(self, myIP):
        self.ip = myIP
        self.nettag = socket.socket()
        self.nettag.settimeout(1)
        self.nettag.bind((myIP, CAR_PROBE_PORT))
        self.nettag.listen(1)
        self.running = True
        self.job = thr.Thread(target=self.idle, name="Echo")
        Echo.instances += 1

    def idle(self):
        while self.running:
            try:
                conn, (ip, port) = self.nettag.accept()
            except socket.timeout:
                pass
            else:
                time.sleep(1)
                msg = unicode(conn.recv(4096))
                print("\nECHO: {}:{} says {}".format(ip, port, msg))
                conn.send("echo-echo{} @ {}".format(self.instances, self.ip))
                conn.shutdown(1)
                conn.close()
        print("ECHO: idle exiting...")

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running:
            self.teardown(1)

if __name__ == '__main__':
    echo = Echo("127.0.0.1" if len(sys.argv) < 2 else sys.argv[1])
    echo.idle()
    command = " "
    while command != "y":
        command = input("Shutdown? y/[n] > ")
