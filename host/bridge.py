from __future__ import print_function, absolute_import, unicode_literals

import time
import threading as thr
from datetime import datetime

from FIPER.generic.interfaces import interface_factory
from FIPER.generic.abstract import (
    AbstractListener, StreamDisplayer, Console
)
from FIPER.generic.messaging import Probe


class Listener(AbstractListener):

    """
    Singleton class!
    Listens for incoming car connections for the server.
    Runs in a separate thread.
    """

    instances = 0

    def __init__(self, master):
        if Listener.instances > 0:
            raise RuntimeError("The Singleton [Listener] is already instantiated!")

        AbstractListener.__init__(self, master.ip, self.handshake)

        self.master = master  # type: FleetHandler
        self.worker = None  # type: thr.Thread

        Listener.instances += 1

    def start(self):
        """
        Creates a new worker thread in case Listener needs to be
        restarted.
        self.run is inherited from AbstractListener
        """
        if self.worker is not None:
            print("{}-Attempted start while already running!")
            return
        self.worker = thr.Thread(target=self.mainloop, name="Server-Listener")
        self.worker.start()

    def teardown(self, sleep=2):
        super(Listener, self).teardown(sleep)
        self.worker = None

    def handshake(self, msock):
        """
        Builds an interface and puts it into the server's appropriate
        container for later usage.
        :param msock: connected socket used for message connection
        """
        ifc = interface_factory(msock, self.dsocket, self.rcsocket)
        if not ifc:
            return
        if ifc.entity_type == "car":
            self.master.cars[ifc.ID] = ifc
        else:
            self.master.clients[ifc.ID] = ifc


# noinspection PyUnusedLocal
class FleetHandler(object):

    """
    Class of the main server.
    Groups together the following concepts:
    - Console is run in the main thread, waiting for and parsing input
    commands.
    - Listener is listening for incomming car connections in a separate thread.
    It also coordinates the creation and validation of new car interfaces.
    - CarInterface instances are stored in the .cars dictionary.
    - StreamDisplayer objects can be attached to CarInterface objects and
    are run in a separate thread each.
    - FleetHandler itself is responsible for sending commands to CarInterfaces
    and to coordinate the shutdown of the cars on this side, etc.
    """

    def __init__(self, myIP):
        self.clients = {}
        self.ip = myIP
        self.cars = {}
        self.watchers = {}
        self.since = datetime.now()
        self._cars_online = "Unknown, use 'sweep' to find out!"

        self.listener = Listener(self)
        self.console = Console("FIPER-Server", **{
            "cars": self.printout_cars,
            "kill": self.kill_car,
            "watch": self.watch_car,
            "unwatch": self.stop_watch,
            "shutdown": self.shutdown,
            "status": self.report,
            "message": self.message,
            "probe": self.probe,
            "connect": self.connect,
            "sweep": self.sweep
        })

        self.status = "Idle"
        print("SERVER: online")

    def printout_cars(self, *args):
        """List the current car-connections"""
        print("Cars online:\n{}\n".format("\n".join(self.cars)))

    def connect(self, *ips):
        """Initiate connection with the supplied ip address(es)"""
        Probe.initiate(*ips)

    def probe(self, *ips):
        """Probe the supplied ip address(es)"""
        Probe.probe(*ips)

    def message(self, ID, *msgs):
        """Just supply the car ID, and then the message to send."""
        self.cars[ID].send(" ".join(msgs).encode())

    def sweep(self, *ips):
        """Probe the supplied ip addresses and print the formatted results"""
        if not ips:
            ips = ".".join(self.ip.split(".")[:-1] + ["0-255"])
        IDs = dict(Probe.probe(*ips))

        mxIDlen = max(len(unicode(v)) for v in IDs.values())
        mxIPlen = 3+3+3+3+3
        mxstatlen = 9

        header = ("|{:^{IPlen}}|{:^{IDlen}}|{:^{statlen}}|\n".format(
            "IP", "ID", "status", IPlen=mxIPlen, IDlen=mxIDlen, statlen=mxstatlen)
        )
        table = ""
        separator = ("+" + "-"*mxIPlen +
                     "+" + "-"*mxIDlen +
                     "+" + "-"*mxstatlen + "+\n")
        buildme = "|{:^{IPlen}}|{:^{IDlen}}|{:^{statlen}}|\n"

        for IP, ID in ((k, v) for k, v in IDs.iteritems() if v is not None):
            status = ("connected" if ID in self.cars else "idle")
            table += separator
            table += (buildme.format(
                IP, ID, status, IPlen=mxIPlen, IDlen=mxIDlen, statlen=mxstatlen)
            )
        for IP, _ in ((k, v) for k, v in IDs.iteritems() if v is None):
            table += separator
            table += (buildme.format(
                IP, "-", "offline", IPlen=mxIPlen, IDlen=mxIDlen, statlen=mxstatlen)
            )

        table = ((separator + header + table + separator)
                 if table else
                 "No cars on the specified region!")

        self._cars_online = table
        print(table)

    def kill_car(self, ID, *args):
        """Sends a shutdown message to a remote car, then tears down the connection"""
        if ID not in self.cars:
            print("SERVER: no such car:", ID)
            return
        if ID in self.watchers:
            self.stop_watch(ID)
        carifc = self.cars[ID]
        carifc.send("shutdown")
        time.sleep(3)

        status = carifc.recv()
        if status is None:
            print("SERVER: car-{} didn't shut down as expected!".format(ID))
        elif status == "{} offline".format(ID):
            print("SERVER: car-{} shut down as expected".format(ID))
        else:
            print("SERVER: received unknown status from car-{}: {}"
                  .format(ID, status))

        del self.cars[ID]

    def watch_car(self, ID, *args):
        """Initializes streaming via StreamDisplayer in a separate thread"""
        if ID not in self.cars:
            print("SERVER: no such car [{}]".format(ID))
            return
        if ID in self.watchers:
            print("SERVER: already watching", ID)
            return
        self.cars[ID].send("stream on")
        time.sleep(1)
        self.watchers[ID] = StreamDisplayer(self.cars[ID])

    def stop_watch(self, ID, *args):
        """Tears down the StreamDisplayer and shuts down a stream"""
        if ID not in self.watchers:
            print("SERVER: {} is not being watched!".format(ID))
            return
        self.cars[ID].send("stream off")
        self.watchers[ID].teardown()
        time.sleep(3)
        del self.watchers[ID]

    def shutdown(self, *args):
        """Shuts the server down, terminating all threads nicely"""

        self.listener.teardown(1)

        for ID, car in sorted(self.cars.items()):
            if ID in self.watchers:
                self.stop_watch(ID)
            car.send("shutdown")

        rounds = 0
        while self.cars:
            print("SERVER: Car corpse collection round {}/{}".format(rounds+1, 4))
            time.sleep(3)
            for ID, car in sorted(self.cars.items()):
                msg = car.recv()
                if msg != "car-{}:offline".format(ID):
                    print("SERVER: Received wrong corpse message:", msg)
                    continue
                self.cars[ID].teardown()
                del self.cars[ID]

            if rounds >= 3:
                print("SERVER: cars: [{}] didn't shut down correctly"
                      .format(", ".join(self.cars.keys())))
                break
            rounds += 1
        else:
            print("SERVER: All cars shut down correctly!")
        print("SERVER: Exiting...")

    def report(self, *args):
        """
        Prints a nice server status report
        """
        repchain = "FIPER Server\n"
        repchain += "-" * (len(repchain) - 1) + "\n"
        repchain += "Up since " + self.since.strftime("%Y.%m.%d %H:%M:%S") + "\n"
        repchain += "Cars online: {}\n".format(len(self.cars))
        print("\n" + repchain + "\n")
