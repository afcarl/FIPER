from __future__ import unicode_literals, print_function, absolute_import

import socket

# Ports
STREAM_SERVER_PORT = 1235
MESSAGE_SERVER_PORT = 1234


def getsrv(ip, port, timeout=0):
    s = socket.socket()
    s.bind((ip, port))
    s.listen(1)
    if timeout:
        s.settimeout(timeout)
    return s


def listen(myaddr="127.0.0.1"):
    mserver = getsrv(myaddr, MESSAGE_SERVER_PORT, timeout=1)
    dserver = getsrv(myaddr, STREAM_SERVER_PORT)

    while 1:
        try:
            mconn, addr = mserver.accept()
            break
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            mserver.close()
            dserver.close()
            return
        except Exception as E:
            print("Caught exception:", str(E))
            return
    dconn, addr = dserver.accept()
    return mconn, dconn


def display(mconn, dconn):

