from __future__ import print_function, absolute_import, unicode_literals

import abc
import time
import socket
import threading as thr

from FIPER.generic import CAR_PROBE_PORT


class Messaging(object):

    """
    Wraps a TCP socket, which will be used for two-way
    message-passing between the car and the server.
    """

    def __init__(self, sock, tag=b""):
        """
        :param sock: socket, around which the Messenger is wrapped
        :param tag: optional tag, concatenated to the beginning of every message
        """
        self.tag = tag
        self.recvbuffer = []
        self.sendbuffer = []
        self.sock = sock  # type: socket.socket
        self.job_in = thr.Thread(target=self.flow_in)
        self.job_out = thr.Thread(target=self.flow_out)

        if self.sock.gettimeout() <= 0:
            print("MESSENGER: socket received has timeout:", self.sock.gettimeout())
            print("MESSENGER: setting it to 1")
            self.sock.settimeout(1)

        self.running = True
        self.job_in.start()
        self.job_out.start()
        print("Messenger workers started!")

    def flow_out(self):
        """
        This method is responsible for the sending of
        messages from the send buffer.
        This is intended to run in a separate thread.
        """
        while self.running:
            if self.sendbuffer:
                msg = self.sendbuffer.pop(0)
                for slc in (msg[i:i+1024] for i in range(0, len(msg), 1024)):
                    self.sock.send(slc)
            time.sleep(0.5)
        print("Messenger outflow worker exited!")

    def flow_in(self):
        """
        This method is responsible to receive and chop up the
        incoming messages. The messages are stored in the receive
        buffer.
        """
        while self.running:
            data = b""
            while data[-5:] != b"ROGER" and self.running:
                try:
                    slc = self.sock.recv(1024)
                except socket.timeout:
                    pass
                # except socket.error as E:
                #     print("MESSENGER: caught socket exception:", E.message)
                #     self.running = False
                else:
                    data += slc
            if not self.running:
                if data:
                    print("MESSENGER: data left hanging:" + data[:-5].decode("utf8"))
                    return
            data = data[:-5].decode("utf8")
            self.recvbuffer.extend(data.split("ROGER"))
        print("Messenger inflow worker exited!")

    def send(self, *msgs):
        """
        This method prepares and stores the messages in the
        send buffer for sending.
        
        :param msgs: the actual messages to send
        """
        self.sendbuffer.extend([self.tag + m + b"ROGER" for m in msgs])

    def recv(self, n=1, timeout=0):
        """
        This method, when called, returns messages available in
        the receive buffer. The messages are returned in a
        Last-In-First-Out (queue-like) order.
        
        :param n: the number of messages to retreive at once 
        :param timeout: set timeout if no messages are available
        :return: returns the decoded (UTF-8) message or a list of messages
        """
        msgs = []
        for i in range(n):
            try:
                m = self.recvbuffer.pop(0)
            except IndexError:
                if timeout:
                    time.sleep(timeout)
                    try:
                        m = self.recvbuffer.pop(0)
                    except IndexError:
                        msgs.append(None)
                        break
                else:
                    msgs.append(None)
                    break
            msgs.append(m)
        return msgs if len(msgs) > 1 else msgs[0]

    def teardown(self, sleep=3):
        self.running = False
        time.sleep(sleep)
        self.sock.close()
        print("Messenger OUT!")

    def __del__(self):
        if self.running:
            self.teardown()


class Probe(object):
    """
    Mixin / Static class for entities with probing capabilities.
    """

    __metaclass__ = abc.ABCMeta

    @staticmethod
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

    @staticmethod
    def _probe(ip, msg):
        """
        Probes an IP address with a given message.
        This causes the remote car to send back its
        tag, which is validated, then the car ID is
        extracted from it and returned.
        """

        assert unicode(msg) in ("connect", "probing"), "Invalid message!"

        def create_connection():
            while 1:
                try:
                    sock.connect((ip, CAR_PROBE_PORT))
                except socket.timeout:
                    print("PROBE: waiting for remote...")
                except socket.error:
                    return 0
                else:
                    return 1

        def probe_and_receive_tag():
            sock.send(msg)
            for i in range(5, 0, -1):
                try:
                    network_tag = sock.recv(1024)
                except socket.timeout:
                    print("PROBE: no answer {}".format(i))
                else:
                    return network_tag
            else:
                print("PROBE: timed out on", ip)
                return None

        sock = socket.socket()
        sock.settimeout(0.1)

        success = create_connection()
        if not success:
            return ip, None
        tag = probe_and_receive_tag()
        if tag is None:
            return ip, None
        ID = Probe.validate_car_tag(tag, ip)
        if ID is None:
            print("PROBE: invalid car ID from tag: [{}] @ {}"
                  .format(tag, ip))
            return ip, None
        return ip, ID

    @staticmethod
    def probe(*ips):
        """
        Send a <probing> message to the specified IP addresses.
        If the target is a car, it will return its ID, or None otherwise.
        """
        # Sacred docstring. Please don't touch it. :)
        reparsed = []
        for ip in ips:
            reparsed += Probe._reparse_and_validate_ip(ip)
        responses = [Probe._probe(ip, b"probing") for ip in reparsed]
        return responses[0] if len(responses) == 1 else responses

    @staticmethod
    def initiate(*ips):
        """
        Send a <connect> message to the specified IP addresses.
        The target car will initiate connection to this server/client.
        """
        # Sacred docstring. Please don't touch it. :)
        reparsed = []
        for ip in ips:
            reparsed += Probe._reparse_and_validate_ip(ip)
        responses = [Probe._probe(ip, b"connect") for ip in ips]
        return responses[0] if len(responses) == 1 else responses

    @staticmethod
    def _reparse_and_validate_ip(ip):
        msg = "PROBE: invalid IP!"
        splip = ip.split(".")
        if len(splip) != 4:
            return [None]
        found_hyphen = 0
        for i, part in enumerate(splip):
            if "-" in part:
                if found_hyphen:
                    print("PROBE: only one part of the IP can be set to a range!")
                    return [None]
                if not all(r.isdigit() for r in part.split("-")):
                    print(msg, "Found non-digit in range!")
                    return [None]
                found_hyphen = i
            else:
                if not part.isdigit():
                    print(msg, "Found non-digit:", part)
                    return [None]
        if found_hyphen:
            start, stop = splip[found_hyphen].split("-")
            return [".".join(splip[:found_hyphen] + [str(i)] + splip[found_hyphen+1:])
                    for i in range(int(start), int(stop))]
        return [ip]
