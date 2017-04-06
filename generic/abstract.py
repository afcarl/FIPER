import socket

import time

from . import srvsock, MESSAGE_SERVER_PORT, STREAM_SERVER_PORT, RC_SERVER_PORT


class AbstractListener(object):
    """
    Mixin class for an entity to promote it
    to central servership.
    """

    def __init__(self, myIP, callback_on_connection):
        self.msocket = srvsock(myIP, MESSAGE_SERVER_PORT, timeout=3)
        self.dsocket = srvsock(myIP, STREAM_SERVER_PORT)
        self.rcsocket = srvsock(myIP, RC_SERVER_PORT, timeout=1)
        self.running = False
        self.callback = callback_on_connection

    def run(self):
        try:
            self.mainloop()
        except:
            raise
        finally:
            self.teardown()

    def mainloop(self):
        while self.running:
            try:
                conn, addr = self.msocket.accept()
            except socket.timeout:
                pass
            else:
                print("\nABS_LISTENER: Received connection from {}:{}\n"
                      .format(*addr))
                self.callback(conn)
        self.teardown()

    def teardown(self, sleep=2):
        self.running = False
        time.sleep(sleep)
        self.msocket.close()
        self.dsocket.close()
        self.rcsocket.close()

    def __del__(self):
        if self.running:
            self.teardown(2)
