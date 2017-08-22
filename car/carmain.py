"""
Coordinates the first part of the bootstrap process of a car.
Parses arguments (readargs) and waits for server probes (idle).
"""

from __future__ import absolute_import, unicode_literals, print_function

import sys

from FIPER.car.car import TCPCar


def readargs():
    if len(sys.argv) == 4:
        return sys.argv[1:4]

    pleading = "Please supply "
    question = ["the local IP address of this Car",
                "a unique ID for this Car",
                "the IP of a running server [optional]"]
    return [raw_input(pleading + q + " > ") for q in question]


def debugmain():
    ID = "TestCar" if len(sys.argv) == 1 else sys.argv[1]
    lightning_mcqueen = TCPCar(myID=ID, myIP="127.0.0.1")
    lightning_mcqueen.mainloop()


def main():
    localIP, carID = readargs()
    lightning_mcqueen = TCPCar(myID=carID, myIP=localIP)
    lightning_mcqueen.mainloop()


if __name__ == '__main__':
    debugmain()
    print(" -- END PROGRAM --")
