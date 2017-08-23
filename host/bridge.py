from __future__ import print_function, absolute_import, unicode_literals

# stdlib imports
import time
from datetime import datetime

# project imports
from FIPER.generic.subsystem import StreamDisplayer
from FIPER.generic.util import Table
from FIPER.generic.probeclient import Probe
from FIPER.host.component import Listener, Console


# noinspection PyUnusedLocal
class FleetHandler(object):

    """
    Class of the main server.
    Groups together the following concepts:
    - Console is run in the main thread, waiting for and parsing input commands.
    - Listener is listening for incomming car connections in a separate thread.
    It also coordinates the creation and validation of new car interfaces.
    - CarInterface instances are stored in the .cars dictionary.
    - StreamDisplayer objects can be attached to CarInterface objects and
    are run in a separate thread each.
    - FleetHandler itself is responsible for sending commands to CarInterfaces
    and to coordinate the shutdown of the cars on this side, etc.
    """

    the_one = None

    def __init__(self, myIP):
        self.clients = {}
        self.ip = myIP
        self.cars = {}
        self.watchers = {}
        self.since = datetime.now()

        self.status = "Idle"
        self.console = Console(
            master_name="FIPER-Server",
            status_tag=self.status,
            commands_dict={
                "cars": self.printout_cars,
                "kill": self.kill_car,
                "watch": self.watch_car,
                "unwatch": self.stop_watch,
                "shutdown": self.shutdown,
                "status": self.report,
                "message": self.message,
                "probe": self.probe,
                "connect": Probe.initiate,
                "sweep": self.sweep
            }
        )

        self.listener = Listener(self)
        self.listener.start()
        print("SERVER: online")

    def mainloop(self):
        self.console.mainloop()

    def printout_cars(self, *args):
        """List the current car-connections"""
        print("Cars online:\n{}\n".format("\n".join(self.cars)))

    @staticmethod
    def probe(*ips):
        """Probe the supplied ip address(es)"""
        IDs = dict(Probe.probe(*ips))
        for ID, IP in IDs.iteritems():
            print("{:<15}: {}".format(IP, ID if ID else "-"))

    def message(self, ID, *msgs):
        """Just supply the car ID, and then the message to send."""
        self.cars[ID].send(" ".join(msgs).encode())

    @staticmethod
    def sweep(*ips):
        """Probe the supplied ip addresses and print the formatted results"""

        def get_status(dID):
            status = ""
            if dID is None:
                status = "offline"
            else:
                status = "available"
            return status

        if not ips:
            print("[sweep]: please specify an IP address range!")
            return
        IDs = dict(Probe.probe(*ips))
        tab = Table(["IP", "ID", "status"],
                    [3*5, max(len(unicode(v)) for v in IDs.itervalues()), 11])
        for IP, ID in IDs.iteritems():
            tab.add(IP, ID, get_status(ID))

        print(tab.get())

    def kill_car(self, ID, *args):
        """Sends a shutdown message to a remote car, then tears down the connection"""
        if ID not in self.cars:
            print("SERVER: no such car:", ID)
            return
        if ID in self.watchers:
            self.stop_watch(ID)
        success = self.cars[ID].teardown(sleep=1)
        if success:
            del self.cars[ID]

    def watch_car(self, ID, *args):
        """Launches the stream display in a separate thread"""
        if ID not in self.cars:
            print("SERVER: no such car:", ID)
            return
        if ID in self.watchers:
            print("SERVER: already watching", ID)
            return
        self.cars[ID].send(b"stream on")
        time.sleep(1)
        self.watchers[ID] = StreamDisplayer(self.cars[ID])

    def stop_watch(self, ID, *args):
        """Tears down the StreamDisplayer and shuts down a stream"""
        if ID not in self.watchers:
            print("SERVER: {} is not being watched!".format(ID))
            return
        self.cars[ID].send(b"stream off")
        self.watchers[ID].teardown(sleep=1)
        del self.watchers[ID]

    def shutdown(self, *args):
        """Shuts the server down, terminating all threads nicely"""

        self.listener.teardown(1)

        rounds = 0
        while self.cars:
            print("SERVER: Car corpse collection round {}/{}".format(rounds+1, 4))
            for ID in self.cars:
                if ID in self.watchers:
                    self.stop_watch(ID)
                self.kill_car(ID)

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

    def __enter__(self, srvinstance):
        """Context enter method"""
        if FleetHandler.the_one is not None:
            FleetHandler.the_one = srvinstance
        else:
            raise RuntimeError("Only one can remain!")
        return srvinstance

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context exit method, ensures proper shutdown"""
        if FleetHandler.the_one is not None:
            FleetHandler.the_one.shutdown()
            FleetHandler.the_one = None
