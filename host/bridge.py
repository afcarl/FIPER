from __future__ import print_function, absolute_import, unicode_literals

import time
import threading as thr
from datetime import datetime

from FIPER.generic.routines import srvsock
from FIPER.generic.interfaces import interface_factory
from FIPER.generic.abstract import AbstractListener, StreamDisplayer


class Console(thr.Thread):

    """
    Singleton class!
    Abstraction of the server's console.
    """

    instances = 0

    def __init__(self, master):
        """
        :param master: FleetHandler (server) object
        """
        if Console.instances > 0:
            raise RuntimeError("The Singleton [Console] is already instantiated!")
        thr.Thread.__init__(self, name="Server-console")
        self.master = master
        self.commands = {
            "help": lambda: print("Available commands:", ", "
                                  .join(sorted(self.commands))),
            "cars": lambda: print("Cars online:", ", "
                                  .join(sorted(self.master.cars))),
            "kill": self.master.kill_car,
            "watch": self.master.watch_car,
            "unwatch": self.master.stop_watch,
            "shutdown": self.master.shutdown,
            "status": self.master.report,
            "start": self.master.listener.start,
            "message": lambda ID, *msg: self.master.cars[ID].send(
                b" ".join((w.encode() for w in msg)))
        }
        Console.instances += 1

    @property
    def prompt(self):
        return "FIPER bridge [{}] > ".format(self.master.status)

    def run(self):
        """
        Server console main loop (and program main loop)
        """
        while 1:
            cmd, args = self.read_cmd()
            if not cmd:
                continue
            elif cmd == "shutdown":
                break
            else:
                try:
                    self.commands[cmd](*args)
                except Exception as E:
                    print("CONSOLE: The command [{}] caused exception: {}".format(cmd, E.message))
                    print("CONSOLE: Ignoring commad!")
        self.master.shutdown()
        print("SERVER: Console shut down correctly")

    def read_cmd(self):
        c = raw_input(self.prompt).split(" ")
        cmd = c[0].lower()
        if len(c) > 1:
            args = c[1:]
        else:
            args = ""
        return cmd, args

    def cmd_parser(self, cmd, args):
        if cmd[0] not in self.commands:
            print("SERVER: Unknown command:", cmd)
        else:
            self.commands[cmd](*args)


class Listener(AbstractListener):

    """
    Singleton class!
    Listens for incoming car connections for the server.
    """

    instances = 0

    def __init__(self, master):
        if Listener.instances > 0:
            raise RuntimeError("The Singleton [Listener] is already instantiated!")

        AbstractListener.__init__(self, master.ip, self._coordinate_handshake)

        self.master = master  # type: FleetHandler
        self.msocket, self.dsocket, self.rcsocket = [
            srvsock(master.ip, typ, tmt) for typ, tmt in zip("msr", (3, None, 1))
        ]
        self.worker = None

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
        self.worker = thr.Thread(target=self.run, name="Server-Listener")
        self.worker.start()

    def teardown(self, sleep=2):
        super(Listener, self).teardown(sleep)
        self.worker = None

    def _coordinate_handshake(self, msock):
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

    def __init__(self, ip):
        self.clients = {}
        self.ip = ip
        self.cars = {}
        self.watchers = {}
        self.since = datetime.now()

        self.listener = Listener(self)
        self.console = Console(self)

        self.running = False
        self.status = "Idle"

    def kill_car(self, ID, *args):
        """
        Sends a shutdown message for a remote car, then
        tears down the connection and does the cleanup.
        """
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
            print("SERVER: Car-{} didn't shut down as expected!".format(ID))
        elif status == "{} offline".format(ID):
            print("SERVER: Car-{} shut down as expected".format(ID))
        else:
            print("SERVER: received unknown status from Car-{}: {}"
                  .format(ID, status))

        del self.cars[ID]

    def watch_car(self, ID, *args):
        """
        Initializes streaming, then launches a StreamDisplayer,
        which is run in a separate thread.
        """

        self.cars[ID].send("stream on")
        time.sleep(3)
        self.watchers[ID] = StreamDisplayer(self.cars[ID])

    def stop_watch(self, ID, *args):
        """
        Tears down the StreamDisplayer and shuts down a stream
        """
        self.cars[ID].send("stream off")
        self.watchers[ID].running = False
        time.sleep(3)
        del self.watchers[ID]

    def shutdown(self, *args):
        """
        Shuts the server down, terminates all threads and
        does the necessary cleanup
        """
        self.running = False

        exits = [None]*len(self.cars)

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

    def report(self, *args):
        """
        Prints a nice server status report
        """
        repchain = ("Online " if self.running else "Offline ")
        repchain += "FIPER Server\n"
        repchain += "-" * (len(repchain) - 1) + "\n"
        repchain += "Up since " + self.since.strftime("%Y.%m.%d %H:%M:%S") + "\n"
        repchain += "Cars online: {}\n".format(len(self.cars))
        print("\n" + repchain + "\n")


def readargs():
    pleading = "Please supply "
    question = ["the local IP address of this server"]
    return [raw_input(pleading + q + " > ") for q in question][0]


def debugmain():
    """Launches the server on localhost"""
    server = FleetHandler("127.0.0.1")
    try:
        server.listener.start()
        server.console.run()
    except Exception as E:
        print("OUTSIDE: exception occured:", E.message)
        server.shutdown("Exception occured: {}\nShutting down!".format(E.message))

    time.sleep(3)
    print("OUTSIDE: Exiting...")


def main():
    """Does the argparse and launches a server"""
    import sys

    if len(sys.argv) == 2:
        serverIP = sys.argv[1]
    else:
        serverIP = readargs()

    server = FleetHandler(serverIP)
    try:
        server.console.run()
    except Exception as E:
        print("OUTSIDE: exception occured:", E.message)
    finally:
        server.shutdown()

    time.sleep(3)
    print("OUTSIDE: Exiting...")


if __name__ == '__main__':
    debugmain()
