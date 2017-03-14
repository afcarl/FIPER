from __future__ import print_function, absolute_import, division, unicode_literals

import time
import socket
import threading as thr
from datetime import datetime

import cv2

from FIPER.host.interfaces import CarInterface
from FIPER.generic import *


class StreamDisplayer(thr.Thread):

    """
    Handles the cv2 displays.
    Currently faulty!
    Multiple streams get mixed up in the same window...
    """

    def __init__(self, carint):
        self.interface = carint
        thr.Thread.__init__(self, target=self.watch)
        self.running = True
        self.online = True
        self.start()

    def watch(self):
        stream = self.interface.get_stream()
        for i, pic in enumerate(stream, start=1):
            self.interface.out("\rRecieved {:>4} frames of shape {}"
                               .format(i, pic.shape), end="")
            cv2.imshow("{} Stream".format(self.interface.car_ID), pic)
            cv2.waitKey(1)
            if not self.running:
                break
        cv2.destroyWindow("{} Stream".format(self.interface.car_ID))
        self.online = False


class Console(thr.Thread):

    """
    Abstraction of the server console.
    """

    def __init__(self, master):
        """
        :param master: FleetHandler (server) object
        """
        thr.Thread.__init__(self, name="Console")
        self.master = master
        self.commands = {
            "help": lambda: print("Available commands:", ", "
                                  .join(sorted(self.commands))),
            "cars": lambda: print("Cars online:", ", "
                                  .join(sorted(self.master.cars))),
            "kill": self.master.kill_car,
            "watch": self.master.watch_car,
            "shutdown": self.master.shutdown,
            "status": self.master.report,
            "start": self.master.listener.start,
            "message": lambda ID, *msg: self.master.cars[ID].send(
                b" ".join((w.encode() for w in msg)))
        }

    @property
    def prompt(self):
        return "FIPER bridge [{}] > ".format(self.master.status)

    def run(self):
        """
        Server console main loop
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
                    print("{} caused: {}".format(cmd, E.message))
                    self.master.shutdown()
                    break
        print("SERVER: Console shut down correctly")

    def read_cmd(self):
        c = raw_input(self.prompt).split(" ")
        cmd, args = c[0].lower(), c[1:]
        return cmd, args

    def cmd_parser(self, cmd, args):
        if cmd[0] not in self.commands:
            print("SERVER: Unknown command:", cmd)
        else:
            self.commands[cmd](*args)


class Listener(thr.Thread):

    instances = 1

    def __init__(self, master):
        thr.Thread.__init__(self, name="Listener-{}".format(Listener.instances))
        self.master = master  # type: FleetHandler

        Listener.instances += 1

    def run(self):
        try:
            self.setup_server()
            self.mainloop()
        except:
            raise
        finally:
            self.teardown()

    def setup_server(self):
        self.master.running = True
        self.master.status = "Listening"
        print("\nSERVER {}: Awaiting connections...\n".format(self.name))
        self.master.msocket.listen(1)

    def mainloop(self):
        while self.master.running:
            try:
                conn, (ip, port) = self.master.msocket.accept()
            except socket.timeout:
                time.sleep(1)
            else:
                print("\nSERVER: Received connection from", ":".join((ip, str(port))), "\n")
                self.add_new_connection(conn, ip)

    def teardown(self):
        self.master.msocket.close()
        print("SERVER {}: exiting".format(self.name))

    def add_new_connection(self, msock, addr):
        # TODO: split this monster into smaller methods
        messenger = Messaging(msock)
        # Introduction is: {entity_type}-{ID}:HELLO;{frY}x{frX}x{frC}
        introduction = messenger.recv(timeout=3)
        print("SERVER: got introduction:", introduction)
        if ":HELLO;" not in introduction:
            raise RuntimeError("Wrong introductory message from a network entity!")
        introduction = introduction.split(":HELLO;")
        entity_type, ID = introduction[0].split("-")
        if entity_type == "car":
            try:
                frameshape = [int(s) for s in introduction[1].split("x")]
            except ValueError:
                raise ValueError("Received wrong frameshape definition from {}!\nGot {}"
                                 .format(ID, introduction[1]))
            if len(frameshape) < 2 or len(frameshape) > 3:
                errmsg = ("Wrong number of dimensions in received frameshape definition.\n" +
                          "Got {} from {}!".format(ID, frameshape))
                raise ValueError(errmsg)
            self.master.cars[ID] = CarInterface(ID, addr, frameshape, messenger, addr)
        else:
            print("Unknown entity type:", entity_type)


class FleetHandler(object):

    """
    Class of the main server.
    Coordinates connection bootsraping, teardown,
    stream display for multiple car-server connections.
    """

    def __init__(self, ip):
        self.ip = ip
        self.cars = {}
        self.watchers = {}
        self.since = datetime.now()

        # Socket for receiving message connections
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.settimeout(3)
        self.msocket.bind((ip, MESSAGE_SERVER_PORT))
        print("SERVER: msocket bound to", ip)

        self.listener = Listener(self)
        self.console = Console(self)

        self.running = False
        self.status = "Idle"

    def kill_car(self, ID, *args):
        """
        Sends a shutdown message for a remote car, then
        tears down the connection and does the cleanup.
        """
        if ID in self.watchers:
            self.stop_watch(ID)
        carifc = self.cars[ID]
        carifc.send("shutdown")
        time.sleep(3)

        status = carifc.recv()
        if status is None:
            print("SERVER: {} didn't shut down as expected!".format(ID))
        elif status == "{} offline".format(ID):
            print("SERVER {} shut down as expected".format(ID))
        else:
            assert False, "Shame on YOU, Developer!"

        del self.cars[ID]

    def watch_car(self, ID, *args):
        """
        Initializes streaming, then launches a StreamDisplayer,
        which is run by a separate thread.
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
        for ID, car in sorted(self.cars.items()):
            car.send("shutdown")
            if ID in self.watchers:
                self.stop_watch(ID)

        rounds = 0
        while self.cars:
            time.sleep(3)
            for ID, car in sorted(self.cars.items()):
                msg = car.recv()
                if msg != "{} offline".format(ID):
                    continue
                self.cars[ID].messenger.running = False
                self.cars[ID].dsocket.close()
                del self.cars[ID]

            if rounds >= 3:
                print("SERVER: {} didn't shut down correnctly"
                      .format(", ".join(self.cars.keys())))
                break
        else:
            print("SERVER: All cars shut down correctly!")

        self.running = False

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
    main()
