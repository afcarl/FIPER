from __future__ import print_function

import time
import threading as thr


class Messaging(object):
    """
    Groups the messaging connections together
    """

    def __init__(self, sock):
        self.recvbuffer = []
        self.sendbuffer = []
        self.sock = sock
        self.job_in = thr.Thread(target=self.flow_in)
        self.job_out = thr.Thread(target=self.flow_out)

        self.running = True
        self.job_in.start()
        self.job_out.start()
        print("Messenger workers started!")

    def flow_out(self):
        """This method will be run in a separate thread"""
        while self.running:
            if self.sendbuffer:
                msg = self.sendbuffer.pop(0)
                for slc in (msg[i:i+1024] for i in range(0, len(msg), 1024)):
                    self.sock.send(slc)
            time.sleep(0.5)
        print("Messenger outflow worker exited!")

    def flow_in(self):
        while self.running:
            data = b""
            while data[-5:] != b"ROGER":
                slc = self.sock.recv(1024)
                data += slc
            data = data[:-5].decode("utf8")
            self.recvbuffer.extend(data.split("ROGER"))
        print("Messenger inflow worker exited!")

    def send(self, *msgs):
        self.sendbuffer.extend([m + b"ROGER" for m in msgs])

    def recv(self, n=1):
        return self.recvbuffer.pop(0) if n < 1 else self.recvbuffer[:n]
