import time


class Messaging(object):
    """
    Groups the messaging connections together
    """

    @staticmethod
    def send(msock, msg, wait=0.5):
        for slc in (msg[i:i+1024] for i in range(0, len(msg), 1024)):
            msock.send(slc)
        msock.send(b"ROGER")
        time.sleep(wait)

    @staticmethod
    def recv(msock, timeout=0):
        data = b""
        msgbuffer = []
        while data[-5:] != b"ROGER":
            slc = msock.recv(1024)
            if timeout and not slc:
                time.sleep(timeout)
                slc = msock.recv(1024)
                if not slc:
                    return None
            data += slc
        return data[:-5].decode("utf8")
