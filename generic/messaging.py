from __future__ import print_function, absolute_import, unicode_literals

import socket
import time
import threading as thr


class Messaging(object):

    """
    Wraps a TCP socket, which will be used for two-way
    message-passing between the car and the server.
    """

    def __init__(self, sock, tag=b""):
        """
        :param sock: socket, around which the Messenger is wrapped
        :param tag: optional tag, concatenated to the beginning of every message
        """
        self.tag = tag
        self.recvbuffer = []
        self.sendbuffer = []
        self.sock = sock  # type: socket.socket
        self.job_in = thr.Thread(target=self.flow_in)
        self.job_out = thr.Thread(target=self.flow_out)

        self.running = True
        self.job_in.start()
        self.job_out.start()
        print("Messenger workers started!")

    def flow_out(self):
        """
        This method is responsible for the sending of
        messages from the send buffer.
        This is intended to run in a separate thread.
        """
        while self.running:
            if self.sendbuffer:
                msg = self.sendbuffer.pop(0)
                for slc in (msg[i:i+1024] for i in range(0, len(msg), 1024)):
                    self.sock.send(slc)
            time.sleep(0.5)
        print("Messenger outflow worker exited!")

    def flow_in(self):
        """
        This method is responsible to receive and chop up the
        incoming messages. The messages are stored in the receive
        buffer.
        """
        while self.running:
            data = b""
            while data[-5:] != b"ROGER" and self.running:
                try:
                    slc = self.sock.recv(1024)
                except socket.timeout:
                    pass
                # except socket.error as E:
                #     print("MESSENGER: caught socket exception:", E.message)
                #     self.running = False
                else:
                    data += slc
            if not self.running:
                if data:
                    print("MESSENGER: data left hanging:" + data[:-5].decode("utf8"))
                    return
            data = data[:-5].decode("utf8")
            self.recvbuffer.extend(data.split("ROGER"))
        print("Messenger inflow worker exited!")

    def send(self, *msgs):
        """
        This method prepares and stores the messages in the
        send buffer for sending.
        
        :param msgs: the actual messages to send
        """
        self.sendbuffer.extend([self.tag + m + b"ROGER" for m in msgs])

    def recv(self, n=1, timeout=0):
        """
        This method, when called, returns messages available in
        the receive buffer. The messages are returned in a
        Last-In-First-Out (queue-like) order.
        
        :param n: the number of messages to retreive at once 
        :param timeout: set timeout if no messages are available
        :return: returns the decoded (UTF-8) message or a list of messages
        """
        msgs = []
        for i in range(n):
            try:
                m = self.recvbuffer.pop(0)
            except IndexError:
                if timeout:
                    time.sleep(timeout)
                    try:
                        m = self.recvbuffer.pop(0)
                    except IndexError:
                        msgs.append(None)
                        break
                else:
                    msgs.append(None)
                    break
            msgs.append(m)
        return msgs if len(msgs) > 1 else msgs[0]

    def teardown(self, sleep=3):
        self.running = False
        time.sleep(sleep)
        self.sock.close()
        print("Messenger OUT!")

    def __del__(self):
        self.teardown()
