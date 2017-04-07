from __future__ import unicode_literals, print_function, absolute_import

import socket

import numpy as np

from .const import (
    DTYPE, STREAM_SERVER_PORT, MESSAGE_SERVER_PORT, RC_SERVER_PORT
)


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


def srvsock(ip, connection, timeout=None):
    assert connection[0] in "dsmr"
    port = {
        "d": STREAM_SERVER_PORT,
        "s": STREAM_SERVER_PORT,
        "m": MESSAGE_SERVER_PORT,
        "r": RC_SERVER_PORT
    }[connection[0]]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout is not None:
        s.settimeout(timeout)
    s.bind((ip, port))
    s.listen(1)
    return s


def validate_car_tag(tag, address=None):
    tag = unicode(tag)
    print("TAG-VALIDATING:", tag)
    if " @ " not in tag:
        return
    IDs, remote_addr = tag.split(" @ ")
    if address is not None:
        if remote_addr != address:
            print("INVALID CAR TAG: address invalid:")
            print("(expected) {} != {} (got)"
                  .format(address, remote_addr))
    entity_type, ID = IDs.split("-")
    if entity_type != "car":
        print("INVALID CAR TAG: invalid entity type:", entity_type)
        return
    return ID
