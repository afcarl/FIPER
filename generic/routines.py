import numpy as np
from .const import DTYPE


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
