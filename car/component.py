from __future__ import print_function, absolute_import, unicode_literals

# stdlib imports
import time
import socket
import subprocess
import threading as thr

# 3rd party imports
import cv2


# Ports
MESSAGE_SERVER_PORT = 1234
STREAM_SERVER_PORT = 1235

# Stream's tick time:
FPS = 15
SLICESIZE = 1024


class ChannelBase(object):

    def __init__(self):
        self.sock = None
        self.running = False
        self.worker = None

    def _connectbase(self, IP, port, timeout):
        self.sock = socket.create_connection((IP, port), timeout=timeout)

    def start(self):
        if self.sock is None:
            print("{}: object unitialized!".format(self.type))
            return
        if not self.running:
            print("Starting new {} thread!".format(self.type))
            self.worker = thr.Thread(target=self.run, name="Streamer")
            self.worker.start()

    def run(self):
        raise NotImplementedError

    def stop(self):
        self.running = False
        self.worker = None

    def teardown(self, sleep=0):
        self.stop()
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        time.sleep(sleep)

    @property
    def type(self):
        return self.__class__.__name__


class RCReceiver(ChannelBase):

    def __init__(self):
        super(RCReceiver, self).__init__()
        self._recvbuffer = []

    def connect(self, IP):
        super(RCReceiver, self)._connectbase(IP, RC_SERVER_PORT, timeout=1)
        print("RCRECEIVER: connected to {}:{}".format(IP, RC_SERVER_PORT))

    def run(self):
        print("RC: online")
        self.running = True
        commands = []
        while self.running:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                continue
            except Exception as E:
                print("RCRECEIVER: caught exception:", str(E))
                continue

            data = data.decode("utf-8").split(";")
            commands.extend(data)
            if len(commands) >= 10:
                print("".join(commands))
                commands = []

        print("RCReceiver: socket closed, worker deleted! Exiting...")


class TCPStreamer(ChannelBase):

    def __init__(self):
        super(TCPStreamer, self).__init__()
        self._frameshape = None
        self.eye = CaptureDevice()
        self._determine_frame_shape()
        print("TCPSTREAMER: online")

    def connect(self, IP):
        super(TCPStreamer, self)._connectbase(IP, STREAM_SERVER_PORT, None)
        print("TCPSTREAMER: connected to {}:{}".format(IP, STREAM_SERVER_PORT))

    @property
    def frameshape(self):
        return str(self._frameshape)[1:-1].replace(", ", "x")

    def _determine_frame_shape(self):
        self.eye.open()
        success, frame = self.eye.read()
        if not success:
            success, frame = self._fall_back_to_white_noise_stream()
        self._frameshape = frame.shape
        self.eye.close()

    def _fall_back_to_white_noise_stream(self):
        print("TCPSTREAMER: Capture device unreachable, falling back to white noise stream!")
        self.eye = CaptureDevice()
        return self.eye.read()

    def run(self):
        """
        Obtain frames from the capture device via OpenCV.
        Send the frames to the UDP client (the main server)
        """
        pushed = 0
        self.eye.open()
        self.running = True
        for success, frame in self.eye.stream():
            ##########################################
            # Data preprocessing has to be done here #
            serial = frame.astype("uint8").tostring()  #
            ##########################################
            self.sock.sendall(serial)
            pushed += 1
            print("Pushed {:>3} frames".format(pushed))
            if not self.running:
                break
            time.sleep(1. / FPS)
        self.eye.close()
        print("TCPStreamer: socket and worker deleted! Exiting...")


class Commander(object):

    def __init__(self, messenger, status_tag="", commands_dict=None, **commands):
        if not commands and not commands_dict:
            print("ABS_COMMANDER no command specified!")
            commands_dict = {} if commands_dict is None else commands_dict
        self.master_name = "Car"
        self.status_tag = status_tag
        self.commands = {}
        if commands_dict:
            self.commands.update(commands_dict)
        self.commands.update(commands)

        if "help" not in self.commands:
            self.commands["help"] = self.help
        if "clear" not in self.commands:
            self.commands["clear"] = lambda: subprocess.call("clear", shell=True)
        if "shutdown" not in self.commands:
            print("No shutdown command provided!")
            self.commands["shutdown"] = self.teardown
        self.running = False
        self.messenger = messenger
        print("COMMANDER: online!")

    def help(self, *args):
        """Who helps the helpers?"""
        if not args:
            print("Available commands:", ", ".join(sorted(self.commands)))
        else:
            for arg in args:
                if arg not in self.commands:
                    print("No such command: [{}]".format(arg))
                    return
                else:
                    hlp = self.commands[arg].__doc__
                    if hlp is None:
                        print("No help for the [{}] command :(".format(arg))
                    hlp = hlp.replace("\n", " ").replace("\t", " ").strip()
                    print("Docstring for [{}]: {}".format(arg, hlp))

    @property
    def prompt(self):
        mfx = "[{}]".format(self.status_tag) if self.status_tag else ""
        return " ".join((self.master_name, mfx, "> "))

    def mainloop(self):
        """
        Server console main loop
        """
        print("ABS_COMMANDER online")
        args = ()

        self.running = True
        while self.running:
            cmd, args = self.read_cmd()
            if not cmd:
                continue
            elif cmd == "shutdown":
                break
            try:
                self.cmd_parser(cmd, *args)
            except Exception as E:
                print("CONSOLE: command [{}] raised: {}"
                      .format(cmd, str(E)))
        self.running = False
        self.commands["shutdown"](*args)
        print("ABS_COMMANDER Exiting...")

    def read_cmd(self):
        m = self.messenger.recv(timeout=1)
        if m is None:
            return None, ()
        m = m.split(" ")
        return m[0], m[1:]

    def cmd_parser(self, cmd, *args):
        if cmd not in self.commands:
            print("CONSOLE: Unknown command:", cmd)
        else:
            self.commands[cmd](*args)

    def teardown(self, sleep=0):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running:
            self.teardown()


class CaptureDevice(object):

    # noinspection PyArgumentList
    def __init__(self, dev=None, dummyfile=0):
        self.device = lambda: cv2.VideoCapture(dummyfile) if dev is None else dev
        self._eye = None

    def open(self):
        self._eye = self.device()

    def read(self):
        if self._eye is None:
            self.open()
        return self._eye.read()

    def stream(self):
        if self._eye is None:
            self.open()
        while self._eye:
            yield self._eye.read()

    def close(self):
        self._eye.release()
        self._eye = None


class Messaging(object):

    def __init__(self, conn, tag=b"", sendtick=0.5):
        """
        :param conn: socket, around which the Messenger is wrapped
        :param tag: optional tag, concatenated to the beginning of every message
        """
        self.tag = tag
        self.sendtick = sendtick
        self.recvbuffer = []
        self.sendbuffer = []
        self.sock = conn
        self.job_in = thr.Thread(target=self._flow_in)
        self.job_out = thr.Thread(target=self._flow_out)

        if self.sock.gettimeout() <= 0:
            print("MESSENGER: socket received has timeout:", self.sock.gettimeout())
            print("MESSENGER: setting it to 1")
            self.sock.settimeout(1)

        self.running = True
        self.job_in.start()
        self.job_out.start()

    @classmethod
    def connect_to(cls, IP, tag=b"", timeout=1):
        addr = (IP, MESSAGE_SERVER_PORT)
        conn = socket.create_connection(addr, timeout=timeout)
        return cls(conn, tag)

    def _flow_out(self):
        print("MESSENGER: flow_out online!")
        while self.running:
            if self.sendbuffer:
                msg = self.sendbuffer.pop(0)
                for slc in (msg[i:i + SLICESIZE] for i in range(0, len(msg), 1024)):
                    self.sock.send(slc)
            time.sleep(self.sendtick)
        print("MESSENGER: flow_out exiting...")

    def _flow_in(self):
        print("MESSENGER: flow_in online!")
        while self.running:
            data = b""
            while data[-5:] != b"ROGER" and self.running:
                try:
                    slc = self.sock.recv(SLICESIZE)
                except socket.timeout:
                    time.sleep(0.1)
                except socket.error as E:
                    print("MESSENGER: caught socket exception:", E)
                    self.teardown(1)
                except Exception as E:
                    print("MESSENGER: generic exception:", E)
                    self.teardown(1)
                else:
                    data += slc
            if not self.running:
                if data:
                    print("MESSENGER: data left hanging:" + data[:-5].decode("utf8"))
                    return
            data = data[:-5].decode("utf8")
            self.recvbuffer.extend(data.split("ROGER"))
        print("MESSENGER: flow_in exiting...")

    def send(self, *msgs):
        assert all(isinstance(m, bytes) for m in msgs)
        self.sendbuffer.extend([self.tag + m + b"ROGER" for m in msgs])

    def recv(self, n=1, timeout=0):
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

    def teardown(self, sleep=0):
        self.running = False
        time.sleep(sleep)
        self.sock.close()

    def __del__(self):
        if self.running:
            self.teardown()
