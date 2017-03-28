import numpy as np

# Ports
STREAM_SERVER_START_PORT = 2000  # incremented for every car
MESSAGE_SERVER_PORT = 1234

# Stream's tick time in seconds:
TICK = .1

# Standard RGB data type, 0-255 unsigned int
DTYPE = np.uint8

# Addresses
BEAST = "192.168.1.2"
NOTE = "192.168.1.5"
PI = "192.168.1.121"
