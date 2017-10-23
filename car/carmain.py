"""
Coordinates the first part of the bootstrap process of a car.
Parses arguments (readargs) and waits for server probes (idle).
"""

import sys

from FIPER.car.car import TCPCar


ip = sys.argv[-1] if len(sys.argv) == 2 else "127.0.0.1"
car = TCPCar("WebSummitCar")
car.run(ip)
