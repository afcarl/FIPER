from __future__ import print_function, unicode_literals, absolute_import

import time
import socket as sck

from FIPER.generic.const import CAR_PROBE_PORT
from FIPER.generic.routines import validate_car_tag
from FIPER.generic.interfaces import interface_factory
from FIPER.generic.abstract import AbstractListener, StreamDisplayer


class DirectConnection(AbstractListener):

    def __init__(self, myIP):
        """
        :param myIP: the local IP address
        """
        super(DirectConnection, self).__init__(myIP, self._listener_callback)
        self.target = None
        self.interface = None
        self.streamer = None  # type: StreamDisplayer
        self.streaming = False

    def _listener_callback(self, msock):
        """
        This method is called by AbstractListener.run() on the newly
        created message-connection socket which creates the messaging
        channel between the remote car and this class.
        """
        self.interface = interface_factory(msock, self.dsocket, self.rcsocket)
        self.running = False

    def connect(self, ip):
        """
        Coordinates the bootstrapping of a car-server connection.
        Groups together the following routines:
        - self._probe:
        -- sends a connect message to the car
        -- receives and validates 
        """
        self._probe(ip, "connect")
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
        self.streaming = True
        if self.interface is None:
            print("DirectConnection: no interface!")
            return
        self.interface.send("stream on")
        self.streamer = StreamDisplayer(self.interface)

    def stop_stream(self):
        self.interface.send("stream off")
        self.streamer.teardown(1)
        self.streamer = None
        self.streaming = False

    @staticmethod
    def _probe(ip, msg):
        """
        Probes an IP address with a given message.
        This causes the remote car to send back its
        tag, which is validated, then the car ID is
        extracted from it and returned.
        """

        assert unicode(msg) in ("connect", "probing"), "Invalid message!"

        def setup_socket():
            s = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
            s.settimeout(1)
            return s

        def create_connection(s):
            while 1:
                try:
                    s.connect((ip, CAR_PROBE_PORT))
                except sck.timeout:
                    print("DirectConnection: waiting for remote...")
                except sck.error:
                    print("DirectConnection: invalid address: ", ip)
                    return None
                else:
                    return s

        def probe_and_receive_tag(s):
            s.sendall(msg)
            for i in range(10):
                try:
                    network_tag = s.recv(1024)
                except sck.timeout:
                    pass
                else:
                    return network_tag
            else:
                print("DirectConnection: Couldn't connect to car @", ip)
                return None

        sock = setup_socket()
        sock = create_connection(sock)
        if sock is None:
            return
        tag = probe_and_receive_tag(sock)
        if tag is None:
            return
        ID = validate_car_tag(tag, ip)
        if ID is None:
            print("DirectConnection: invalid car ID from tag: [{}] @ {}"
                  .format(tag, ip))
            return
        return ID

    @staticmethod
    def probe(ip):
        return DirectConnection._probe(ip, b"probing")

    def teardown(self, sleep=2):
        print("DC: teardown called!")
        if self.streaming:
            self.stop_stream()
        if self.interface is not None:
            self.interface.send("shutdown")
            time.sleep(1)
            self.interface.teardown()
        super(DirectConnection, self).teardown(sleep)


if __name__ == '__main__':
    LH = "127.0.0.1"
    dc = DirectConnection(LH)
    for probe in range(3, -1, -1):
        remote_ID = dc.probe(LH)
        print("PROBE-{}: reponse: {}".format(probe, remote_ID))
        time.sleep(3)
        if remote_ID is not None:
            break
    dc.connect(LH)
    dc.display_stream()
    while 1:
        v = unicode(raw_input("> "))
        if v == "quit":
            dc.stop_stream()
            dc.teardown(3)
            break
    print(" -- END PROGRAM -- ")
