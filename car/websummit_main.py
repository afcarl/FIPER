import sys

from car import TCPCar


car = TCPCar("WebSummitCar")
ip = sys.argv[-1] if len(sys.argv) == 2 else "127.0.0.1"
car._
