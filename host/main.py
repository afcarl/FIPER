from __future__ import print_function, unicode_literals, absolute_import

import time

from FIPER.host.bridge import FleetHandler


def readargs():
    import sys

    if len(sys.argv) == 2:
        return sys.argv[1]
    else:
        return raw_input("Please supply the local IP address of this server > ")


def debugmain():
    """Launches the server on localhost"""

    # No context manager in debugmain, I want to see the exceptions,
    server = FleetHandler("127.0.0.1")
    server.mainloop()  # enter the console mainloop

    time.sleep(3)
    print("OUTSIDE: Exiting...")


def main():
    """Does the argparse and launches a server"""
    serverIP = readargs()

    # Context manager ensures proper shutdown of threads
    # see FleetHandler.__enter__ and __exit__ methods!
    with FleetHandler(serverIP) as server:
        server.mainloop()

    time.sleep(3)
    print("OUTSIDE: Exiting...")


if __name__ == '__main__':
    debugmain()
