from __future__ import print_function, absolute_import, division, unicode_literals

import socket
import threading as thr
import time
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
        self.nextport = STREAM_SERVER_PORT

        # Socket for receiving message connections
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.settimeout(3)
        self.msocket.bind((ip, MESSAGE_SERVER_PORT))
        print("SERVER: msocket bound to", ip)

        # This thread looks for new cars on the network
        self.listener = thr.Thread(name="Listener", target=self.listen)

        self.running = False
        self.status = "Idle"

    def add_new_connection(self, msock, addr):
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
            self.cars[ID] = CarInterface(ID, addr, frameshape, messenger, addr, self.nextport)
        else:
            print("Unknown entity type:", entity_type)
        self.nextport += 1

    def start_listening(self):
        """
        Launches the listener thread,
        which looks for new cars on the network
        """
        self.running = True
        self.status = "Listening"
        self.listener.start()

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

    def console(self):
        """
        Server console main loop
        """
        commands = {
            "help": lambda: print("Available commands:", ", ".join(sorted(commands))),
            "cars": lambda: print("Cars online:", ", ".join(sorted(self.cars))),
            "kill": self.kill_car,
            "watch": self.watch_car,
            "shutdown": self.shutdown,
            "status": self.report,
            "start": self.start_listening,
            "message": lambda ID, *msg: Messaging.send(self.cars[ID].msocket, " ".join(msg))
        }
        while 1:
            prompt = "FIPER bridge [{}] > ".format(self.status)
            c = raw_input(prompt).split(" ")
            cmd, args = c[0].lower(), c[1:]
            if not cmd:
                time.sleep(0.1)
                continue
            if c[0] not in commands:
                print("SERVER: Unknown command:", cmd)
            else:
                # print("SERVER: Reveived command:", cmd)
                commands[cmd](*args)
            if cmd == "shutdown":
                print("SERVER: Console shut down correctly")
                break

    def listen(self):
        """
        Accepts connections from cars
        self.listener runs this in a separate thread
        """
        print("\nSERVER: Awaiting connections...\n")
        self.msocket.listen(1)
        while self.running:
            try:
                conn, (ip, port) = self.msocket.accept()
            except socket.timeout:
                time.sleep(1)
            else:
                print("\nSERVER: Received connection from", ":".join((ip, str(port))), "\n")
                self.add_new_connection(conn, ip)
        self.msocket.close()
        print("SERVER: Listener exiting")


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
        server.console()
    finally:
        server.shutdown()

    time.sleep(3)
    print("OUTSIDE: Exiting...")


if __name__ == '__main__':
    main()
