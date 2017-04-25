from __future__ import print_function, unicode_literals, absolute_import

import sys
import time

from FIPER.generic.interfaces import interface_factory, CarInterface
from FIPER.generic.abstract import (
    AbstractListener
)
from FIPER.generic.subsystems import StreamDisplayer
from FIPER.generic.messaging import Probe


class DirectConnection(AbstractListener):

    def __init__(self, myIP):
        """
        :param myIP: the local IP address
        """
        super(DirectConnection, self).__init__(myIP)
        self.target = None
        self.interface = None
        self.streamer = None  # type: StreamDisplayer
        self.streaming = False

    def callback(self, msock):
        """
        This method is called by AbstractListener.mainloop() on the newly
        created message-connection socket which creates the messaging
        channel between the remote car and this class.
        """
        self.interface = interface_factory(msock, self.dlistener, self.rclistener)
        self.running = False  # Stop the mainloop in AbstractListener

    def connect(self, ip):
        """
        Coordinates the bootstrapping of a car-server connection.
        Groups together the following routines:
        - self._probe:
        -- sends a connect message to the car
        -- receives and validates 
        """
        Probe.initiate(ip)
        self.mainloop()

    def get_stream(self, bytestream=False):
        if self.interface is None:
            raise RuntimeError("No connection available!")
        stream = (self.interface.bytestream()
                  if bytestream else
                  self.interface.framestream())
        for d in stream:
            yield d

    def display_stream(self):
        if self.interface is None:
            print("DirectConnection: no interface!")
            return
        self.interface.send("stream on")
        self.streaming = True
        self.streamer = StreamDisplayer(self.interface)

    def stop_stream(self):
        self.interface.send("stream off")
        self.streamer.teardown(1)
        self.streamer = None
        self.streaming = False

    def teardown(self, sleep=2):
        print("DC: teardown called!")
        if self.streaming:
            self.stop_stream()
        if self.interface is not None:
            self.interface.send("shutdown")
            time.sleep(1)
            self.interface.teardown()
        super(DirectConnection, self).teardown(sleep)


def testrun():
    from random import choice

    def build_connection():
        IP = ("127.0.0.1" if len(sys.argv) == 1 else sys.argv[1])
        dc = DirectConnection(IP)

        # Probe car
        for probe in range(3, -1, -1):
            remote_IP, remote_ID = Probe.probe(IP)
            print("PROBE-{}: reponse: {} from {}"
                  .format(probe, remote_ID, remote_IP))
            time.sleep(3)
            if remote_ID is not None:
                break

        # Connecticut
        dc.connect(IP)
        return dc

    def start_display(dc):
        dc.display_stream()
        while 1:
            v = unicode(raw_input("> "))
            if v == "quit":
                dc.stop_stream()
                dc.teardown(3)
                break

    def test_rc(dc):
        msgs = b">", b"<", b"A", b"V"
        choices = []
        while 1:
            try:
                chc = choice(msgs)
                dc.interface.rcsocket.send(chc)
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except Exception as E:
                print("RC Test caught exception:", E.message)
                break
            if len(choices) >= 50:
                print("".join(choices))
                choices = []
        print("RC Test exiting...")
        dc.teardown(1)

    dcinst = build_connection()
    # start_display(dcinst)
    test_rc(dcinst)
    print(" -- END PROGRAM -- ")


if __name__ == '__main__':
    testrun()
