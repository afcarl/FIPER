"""
Coordinates the first part of the bootstrap process of a car.
Parses arguments (readargs) and waits for server probes (idle).
"""

from __future__ import absolute_import, unicode_literals, print_function

import sys
import socket
import warnings

from FIPER.car.tcp_car import TCPCar


def readargs():
    if len(sys.argv) == 4:
        return sys.argv[1:4]

    pleading = "Please supply "
    question = ["the local IP address of this Car",
                "the remote IP address for the server",
                "a unique ID for this Car"]
    return [raw_input(pleading + q + " > ") for q in question]


def idle(myip, myID):
    """
    Broadcasts the ID of the car if probed.
    Also returns the IP of a probing server if the server
    sends a "probing" message.

    :param myip: the ip address of this car 
    :param myID: a unique string, identifiing this car
    :return: the ip of the server if the server sends a "connect" message
    """

    def read_message_from_probe(sck):
        try:
            m = sck.recv(1024)
        except socket.timeout:
            return
        else:
            return m

    def parse_message(m):
        if (not m) or (m == "probing"):
            return "probing"
        elif m == "connect":
            return m
        else:
            warnings.warn("Invalid probe message: " + m)

    def respond_to_probe(sck, ID, address):
        m = b"CAR-{} @ {}".format(ID, *address)
        sck.sendall(m)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.bind((myip, 1233))
    while 1:
        print("CAR-{}: Awaiting connection... Hit Ctrl-C to break!"
              .format(myID))
        try:
            conn, addr = sock.accept()
        except socket.timeout:
            pass
        else:
            print("NETWORKTAG: probed by {}:{}".format(*addr))
            msg = read_message_from_probe(conn)
            msg = parse_message(msg)
            if msg == "connect":
                return addr[0]
            elif msg == "probing":
                respond_to_probe(conn, myID, myip)
            else:
                pass


def debugmain():
    ID = "TestCar" if len(sys.argv) == 1 else sys.argv[1]
    lightning_mcqueen = TCPCar(ID=ID, address="127.0.0.1", server_ip="127.0.0.1")
    lightning_mcqueen.mainloop()

    print("OUTSIDE: Car was shut down nicely.")


def main():
    localIP, carID = readargs()
    serverIP = idle(localIP, carID)
    lightning_mcqueen = TCPCar(ID=carID, address=localIP, server_ip=serverIP)
    lightning_mcqueen.mainloop()

    print("OUTSIDE: Car was shut down nicely.")


if __name__ == '__main__':
    debugmain()
