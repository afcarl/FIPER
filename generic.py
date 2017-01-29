import numpy as np
import socket

# The order of the dimensions is conventional!
# X, Y, Channel
DUMMY_FRAMESIZE = 640, 480, 3

# Ports
STREAMPORT = 1234
MESSAGEPORT = 1235

# Stream's tick time in seconds:
TICK = .1

# Data transfer network protocol
DPROTOCOL = socket.SOCK_DGRAM  # 'tis UDP
# DPROTOCOL = socket.SOCK_STREAM  # 'tis TCP

# Message transfer network protocol
MPROTOCOL = socket.SOCK_STREAM

# Standard RGB data type, 0-255 unsigned int
DTYPE = np.uint8

# Addresses
BEAST = "192.168.1.2"
NOTE = "192.168.1.5"
PI = "192.168.1.121"


def white_noise(shape):
    return (np.random.randn(*shape) * 255.).astype(DTYPE)


def my_ip():
    """Hack to obtain the local IP address of an entity"""
    from socket import socket, AF_INET, SOCK_DGRAM
    tmp = socket(AF_INET, SOCK_DGRAM)
    tmp.connect(("8.8.8.8", 80))
    address = tmp.getsockname()[0]
    if address is None:
        raise RuntimeError("Unable to determine the local IP address!")
    return address
