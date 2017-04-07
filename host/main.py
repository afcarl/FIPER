from __future__ import print_function, unicode_literals, absolute_import

import time

from FIPER.host.bridge import FleetHandler


def readargs():
    return raw_input("Please supply the local IP address of this server > ")


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
