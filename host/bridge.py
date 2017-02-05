from __future__ import print_function, absolute_import, division

import socket
import threading as thr
from datetime import datetime

import cv2

from FIPER.generic import *


class StreamDisplayer(thr.Thread):

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
        self.join()
        self.online = False


class CarInterface(object):
    """
    Implemented as a video stream CLIENT
    """

    def __init__(self, msock, srvip, rcvport):
        # The server's message socket
        self.msocket = msock
        self.send_message = lambda m, t=0.5: Messaging.send(msock, m, t)
        self.get_message = lambda: Messaging.recv(msock)

        # car_ID and framesize are sent throught the message socket
        self.car_ID = self.get_message()
        self.framesize = [int(s) for s in self.get_message().split("x")]
        self.out("Target ID:", self.car_ID)
        self.out("Framesize:", self.framesize)

        self.dsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dsocket.bind((srvip, rcvport))
        self.out("Stream receiver port bound to {}:{}".format(srvip, rcvport))
        self.send_message(str(rcvport).encode(), t=0.5)

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("IFACE {}: ".format(self.car_ID), *args, sep=sep, end=end)

    def get_stream(self):
        """Generator function that yields the received video frames"""
        datalen = np.prod(self.framesize)
        data = b""
        while 1:
            while len(data) < datalen:
                data += self.dsocket.recv(1024)
            yield np.fromstring(data[:datalen], dtype=DTYPE).reshape(self.framesize)
            data = data[datalen:]

    def __repr__(self):
        return "CarInterface {}".format(self.car_ID)


class FleetHandler(object):
    """
    Handles a Fleet of Cars
    """

    def __init__(self, ip=None):
        self.ip = ip
        self.cars = {}
        self.watchers = {}
        self.since = datetime.now()
        self.nextport = STREAM_SERVER_PORT
        self.msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msocket.settimeout(3)
        self.msocket.bind(((ip if ip is not None else my_ip()), MESSAGE_SERVER_PORT))
        print("SERVER: msocket bound to", ip)

        self.listener = thr.Thread(name="Listener", target=self.listen)

        self.running = False
        self.status = "Idle"

    def start_listening(self):
        self.running = True
        self.status = "Listening"
        self.listener.start()

    def kill_car(self, ID, *args):
        msck = self.cars[ID].msocket
        Messaging.send(msck, "shutdown")
        time.sleep(5)

        status = Messaging.recv(msck, timeout=5)
        if status is None:
            print("SERVER: {} didn't shut down as expected!".format(ID))
        elif status == "{} offline".format(ID):
            print("SERVER {} shut down as expected".format(ID))
        else:
            assert False, "Shame on YOU, Developer!"

    def watch_car(self, ID, *args):
        self.watchers[ID] = StreamDisplayer(self.cars[ID])

    def stop_watch(self, ID, *args):
        self.watchers[ID].running = False
        time.sleep(3)
        assert not self.watchers[ID].online
        del self.watchers[ID]

    def shutdown(self, *args):
        for ID, car in sorted(self.cars.items()):
            Messaging.send(car.msocket, "shutdown", wait=0.1)
            if ID in self.watchers:
                self.stop_watch(ID)

        rounds = 0
        while self.cars:
            time.sleep(3)
            for ID, car in sorted(self.cars.items()):
                msg = Messaging.recv(car.msocket, timeout=0.1)
                if msg != "{} offline".format(ID):
                    continue
                self.cars[ID].msocket.close()
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
        repchain = ("Online " if self.running else "Offline ")
        repchain += "FIPER Server\n"
        repchain += "-" * (len(repchain) - 1) + "\n"
        repchain += "Up since " + self.since.strftime("%Y.%m.%d %H:%M:%S") + "\n"
        repchain += "Cars online: {}".format(len(self.cars))
        print("\n" + repchain + "\n")

    def console(self):
        commands = {
            "help": lambda: print("Available commands:", ", ".join(sorted(commands))),
            "kill": self.kill_car,
            "watch": self.watch_car,
            "shutdown": self.shutdown,
            "status": self.report,
            "start": self.start_listening
        }
        while 1:
            prompt = "FIPER bridge [{}] > ".format(self.status)
            c = raw_input(prompt).split(" ")
            cmd, args = c[0].lower(), c[1:]
            if not cmd:
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
                conn, address = self.msocket.accept()  # Times out!
            except:
                time.sleep(1)
            else:
                print("\nSERVER: Received connection from", address, "\n")
                ifc = CarInterface(conn, self.ip, self.nextport)
                self.cars[ifc.car_ID] = ifc
                self.nextport += 1
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
    server.console()

    time.sleep(3)
    print("OUTSIDE: Exiting...")


if __name__ == '__main__':
    main()
