from __future__ import print_function, unicode_literals, absolute_import

import sys
import time

from FIPER.generic.interface import InterfaceFactory
from FIPER.generic.abstract import AbstractListener
from FIPER.generic.subsystem import StreamDisplayer
from FIPER.generic.probeclient import Probe


class DirectConnection(object):

    """
    Abstraction of a direct connection with a car
    (no server or centralized controller present).
    
    Methods used for interfacing with this class:
    - connect(ip) initiates and builds a connection with a
      TCPCar instance at the supplied IP address.
    - probe(ip) probes the given IP address. If there is a
      TCPCar instance there, the method returns its a list
      containing its [IP, ID]. This method can accept multiple
      addresses or an address range e.g.
      probe("192.168.0.0-100") or probe("192.168.1.1", "192.168.1.5")
    - get_stream() is a generator function, yielding the video
      frames as numpy arrays.
    - display_stream() displays the frames in a cv2 window.
    - stop_stream() tears down the streaming thread.
    - rc_command() sends remote control commands to the car.
    - teardown() disassembles the communacion channels. After calling
      this method, the DirectConnection instance is ready for deletion.
    """

    def __init__(self, myIP):
        """
        :param myIP: the local IP address
        """
        self.target = None
        self.interface = None
        self.streamer = None
        self.streaming = False
        self.listener = self._OneTimeListener(self, myIP)
        self.probeobj = Probe()

    def probe(self, ip):
        _, ID = self.probeobj.probe(ip)[0]
        print("DC: probed {} response: {}".format(ip, ID))
        return ID

    def sweep(self, *ips):
        responses = self.probeobj.probe(*ips)
        print("PROBE RESPONSES:")
        for ip, response in responses:
            print("{}: {}".format(ip, response))
        return responses

    def connect(self, ip):
        """
        Initiates via the probe protocol, then bootstraps the connection
        via AbstractListener.mainloop()
        """
        rIP, rID = Probe.initiate(ip)
        if rIP == ip and rID is not None:
            # Enter AbstractListener's mainloop and bootstrap the connetion
            try:
                self.listener.mainloop()
            except Exception as E:
                print("DC: exception in AbstractListener mainloop:", E)
                return False
            else:
                return True
        else:
            print("DC: invalid response on initiation from {}: {}".format(rIP, rID))
            return False

    def get_stream(self, bytestream=False):
        """
        Generator function used to create an infinite stream of
        A/V data from the CarInterface.
        
        :param bytestream: if set, raw bytes are yielded
         instead of processed frames (numpy arrays)
        """
        if self.interface is None:
            raise RuntimeError("No connection available!")
        stream = (self.interface.bytestream()
                  if bytestream else
                  self.interface.framestream())
        for d in stream:
            yield d

    def display_stream(self):
        if self.interface is None:
            print("DC: no interface! Build a connection first!")
            return
        self.interface.send(b"stream on")
        self.streaming = True
        self.streamer = StreamDisplayer(self.interface)  # launches the thread!

    def stop_stream(self):
        self.interface.send(b"stream off")
        if self.streamer is not None:
            self.streamer.teardown(0)
            self.streamer = None
        self.streaming = False

    def teardown(self, sleep=0):
        if self.streaming:
            self.stop_stream()
        if self.interface is not None:
            self.interface.teardown()
        time.sleep(sleep)

    def rc_command(self, *commands):
        self.interface.rcsocket.sendall(b"".join(commands))

    class _OneTimeListener(AbstractListener):

        def __init__(self, master, myIP):
            super(DirectConnection._OneTimeListener, self).__init__(myIP)
            self.master = master

        def callback(self, msock):
            self.master.interface = InterfaceFactory(
                msock, self.dlistener, self.rclistener
            ).get()
            self.running = False  # Break the mainloop in AbstractListener


def run():

    from random import choice

    def probe_and_connect(dc, IP):

        # Probe car up to 3 times
        for probe in range(3, -1, -1):
            ID = dc.probe(IP)
            print("PROBE-{}: reponse: {} from {}"
                  .format(probe, IP, ID))
            time.sleep(3)
            if ID is not None:
                break
        else:
            # If noone answers, return False success code
            return False

        # Try to build connection, return the success code
        return dc.connect(IP)

    def test_stream(dc):
        print("STREAM TEST online...")
        dc.display_stream()
        while 1:
            # noinspection PyUnboundLocalVariable
            raw_input("Hit <enter> to stop! ")
            dc.stop_stream()
            break
        print("STREAM TEST offline...")

    def test_rc(dc):
        msgs = b">", b"<", b"A", b"V"
        choices = []
        print("RC TEST online...")
        while 1:
            try:
                chc = choice(msgs)
                choices.append(chc)
                dc.rc_command(chc)
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except Exception as E:
                print("RC Test caught exception:", E)
                break
            if len(choices) >= 10:
                print("".join(choices))
                choices = []
        print("RC TEST offline...")

    car_IP = ("127.0.0.1" if len(sys.argv) == 1 else sys.argv[1])
    connection = DirectConnection(car_IP)

    success = probe_and_connect(connection, car_IP)
    if not success:
        return
    test_stream(connection)
    test_rc(connection)
    print(" -- TEARING DOWN -- ")
    connection.teardown(3)
    print(" -- END PROGRAM -- ")


if __name__ == '__main__':
    run()
