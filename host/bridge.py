from __future__ import print_function, absolute_import, unicode_literals

import socket
import threading as thr
import time
from datetime import datetime

from FIPER.generic import *
from FIPER.host.streamhandler import StreamDisplayer
from FIPER.generic.interfaces import CarInterface, ClientInterface


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


class Listener(thr.Thread):

    """
    Singleton class!
    Listens for incoming car connections for the server.
    Coordinates the creation of CarInterface objects.
    """

    instances = 0

    def __init__(self, master):
        if Listener.instances > 0:
            raise RuntimeError("The Singleton [Listener] is already instantiated!")
        thr.Thread.__init__(self, name="Server-Listener")

        self.master = master  # type: FleetHandler
        self._set_up_listener_sockets()
        self.running = False

        Listener.instances += 1

    def run(self):
        try:
            self._set_server_flags_to_running_mode()
            self._main_loop_listening_for_connections()
        except:
            raise
        finally:
            self.teardown()

    def _set_up_listener_sockets(self):
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.settimeout(3)
        self.msocket.bind((self.master.ip, MESSAGE_SERVER_PORT))
        self.msocket.listen(1)
        # Socket for receiving data connections
        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dsocket.bind((self.master.ip, STREAM_SERVER_PORT))
        self.dsocket.listen(1)

    def _set_server_flags_to_running_mode(self):
        self.running = True
        self.master.status = "Listening"
        print("\nLISTENER: Server awaiting connections...\n".format(self.name))

    def _main_loop_listening_for_connections(self):
        while self.running:
            try:
                conn, (ip, port) = self.msocket.accept()
            except socket.timeout:
                time.sleep(1)
            else:
                print("\nSERVER: Received connection from {}:{}\n"
                      .format(ip, port))
                self._coordinate_handshake(conn)
        self.teardown()

    def _coordinate_handshake(self, msock):

        def valid_introduction(intr):
            if ":HELLO;" in intr:
                return True
            print("LISTENER: invalid introduction!")
            return False

        def valid_frame_shape(fs):
            if len(fs) < 2 or len(fs) > 3:
                errmsg = ("Wrong number of dimensions in received frameshape definition.\n" +
                          "Got {} from {}!".format(ID, frameshape))
                print(errmsg)
                return False
            return True

        def parse_introductory_string(s):
            """
            Introduction looks like this:
            {entity_type}-{ID}:HELLO;{frY}x{frX}x{frC}
            """

            s = s.split(":HELLO;")
            etype, remoteID = s[0].split("-")

            try:
                shp = [int(sp) for sp in s[1].split("x")]
            except ValueError:
                print("LISTENER: Received wrong frameshape definition from {}!\nGot {}"
                      .format(remoteID, introduction[1]))
                return None
            return etype, remoteID, shp

        messenger = Messaging(msock)
        introduction = None
        while introduction is None:
            introduction = messenger.recv(timeout=1)
            print("LISTENER: got introduction:", introduction)
        if not valid_introduction(introduction):
            return
        result = parse_introductory_string(introduction)
        entity_type, ID = result[:2]
        if not result:
            return
        if entity_type == "car":
            frameshape = result[2]
            if not valid_frame_shape(frameshape):
                return
            self.master.cars[ID] = CarInterface(
                ID, self.dsocket, messenger, frameshape
            )
        elif entity_type == "client":
            self.master.clients[ID] = ClientInterface(
                ID, self.dsocket, messenger
            )
        else:
            raise RuntimeError("Unknown entity type: " + entity_type)

    def teardown(self):
        self.running = False
        time.sleep(2)
        self.msocket.close()
        self.dsocket.close()

    def __del__(self):
        self.teardown()
        Listener.instances -= 1


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

        # Socket for receiving message connections
        print("SERVER: sockets are bound to {}:{}/{}"
              .format(ip, MESSAGE_SERVER_PORT, STREAM_SERVER_PORT))

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
