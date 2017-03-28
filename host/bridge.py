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
    Untested yet! (Only useful for debug anyways)
    """

    instances = 0

    def __init__(self, carint):
        self.interface = carint
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = True
        self.online = True
        self.start()
        StreamDisplayer.instances += 1

    def run(self):
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

    def __del__(self):
        StreamDisplayer.instances -= 1


class Console(thr.Thread):

    """
    Singleton class!
    Abstraction of the server console.
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
                    print("CONSOLE: The command [{}] caused exception: {}".format(cmd, E.message))
                    print("CONSOLE: Ignoring commad!")
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

    """
    Singleton class!
    Listens for car connections.
    Creates CarInterface objects.
    """

    instances = 0

    def __init__(self, master):
        if Listener.instances > 0:
            raise RuntimeError("The Singleton [Listener] is already instantiated!")
        thr.Thread.__init__(self, name="Sever-Listener".format(Listener.instances))
        self.master = master  # type: FleetHandler

        Listener.instances += 1

    def run(self):
        try:
            self._set_server_flags_to_running_mode()
            self._main_loop_listening_for_car_connections()
        except:
            raise
        finally:
            self._tear_down_connection_on_exit()

    def _set_server_flags_to_running_mode(self):
        self.master.running = True
        self.master.status = "Listening"
        print("\nSERVER {}: Awaiting connections...\n".format(self.name))
        self.master.msocket.listen(1)

    def _main_loop_listening_for_car_connections(self):
        while self.master.running:
            try:
                conn, (ip, port) = self.master.msocket.accept()
            except socket.timeout:
                time.sleep(1)
            else:
                print("\nSERVER: Received connection from", ":".join((ip, str(port))), "\n")
                self._coordinate_handshake_with_car(conn, ip)

    def _tear_down_connection_on_exit(self):
        self.master.msocket.close()
        print("SERVER {}: exiting".format(self.name))

    def _coordinate_handshake_with_car(self, msock, addr):

        def valid_introduction(intr):
            if ":HELLO;" in intr:
                return True
            print("LISTENER: invalid introduction!")
            return False

        def valid_entity_type(et):
            if et == "car":
                return True
            print("LISTENER: unknown entity type:", entity_type)
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
            s = s[0].split(":")
            etype, remoteID = s[0].split("-")

            try:
                shp = [int(s) for s in s[1].split("x")]
            except ValueError:
                print("LISTENER: Received wrong frameshape definition from {}!\nGot {}"
                      .format(remoteID, introduction[1]))
                return None
            return etype, remoteID, shp

        def respond_to_car(msngr):
            msngr.send(b"HELLO-PORT:{}".format(self.master.nextport))

        messenger = Messaging(msock)
        introduction = messenger.recv(timeout=3)
        print("LISTENER: got introduction:", introduction)
        if not valid_introduction(introduction):
            return
        result = parse_introductory_string(introduction)
        if not result:
            return
        entity_type, ID, frameshape = result
        if not all((valid_entity_type(entity_type),
                    valid_frame_shape(frameshape))):
            return
        respond_to_car(messenger)
        self.master.cars[ID] = CarInterface(ID, addr, frameshape, messenger, addr)


# noinspection PyUnusedLocal
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

        self._nextport = STREAM_SERVER_START_PORT

        # Socket for receiving message connections
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.settimeout(3)
        self.msocket.bind((ip, MESSAGE_SERVER_PORT))
        print("SERVER: msocket bound to", ip)

        self.listener = Listener(self)
        self.console = Console(self)

        self.running = False
        self.status = "Idle"

    @property
    def nextport(self):
        self._nextport += 1
        return self._nextport

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
