from __future__ import print_function, unicode_literals, absolute_import

import abc
import time
import socket
import subprocess

from .routine import srvsock


class AbstractInterface(object):

    """
    Base class for all connections,
    where Entity may be some remote network entity
    (like a car or a client).

    Groups together the following concepts:
    - a message-passing TCP channel implemented in generic.messaging
    - a one-way data connection, used to read or forward a data stream
    """

    __metaclass__ = abc.ABCMeta

    entity_type = ""

    def __init__(self, ID, dlistener, rclistener, messenger):
        self.ID = ID
        self.messenger = messenger
        self.send = messenger.send
        self.recv = messenger.recv
        self.remote_ip = None
        self.initiated = False
        try:
            self._accept_connection_and_validate_ip_addresses(dlistener, "Data")
            self._accept_connection_and_validate_ip_addresses(rclistener, "RC")
        except socket.timeout:
            self.initiated = False
        else:
            self.initiated = True

    def _accept_connection_and_validate_ip_addresses(self, sock, typ):
        self.out("Awaiting {} connection...".format(typ))
        conn, addr = sock.accept()
        self.out("{} connection from {}:{}".format(typ, *addr))
        if self.remote_ip:
            if self.remote_ip != addr[0]:
                msg = "Warning! Difference in inbound connection addresses!\n"
                msg += ("Messaging is on {}\nData is on {}\nRC is on {}"
                        .format(self.messenger.sock.getsockname()[0],
                                self.remote_ip, addr[0]))
                raise RuntimeError(msg)
        else:
            self.remote_ip = addr[0]
        if typ == "Data":
            self.dsocket = conn
        else:
            self.rcsocket = conn

    def out(self, *args, **kw):
        """Wrapper for print(). Appends car's ID to every output line"""
        # noinspection PyTypeChecker
        sep, end = kw.get("sep", " "), kw.get("end", "\n")
        print("{}IFACE {}: ".format(self.entity_type.upper(), self.ID),
              *args, sep=sep, end=end)

    def teardown(self, sleep):
        self.messenger.teardown(sleep)
        self.dsocket.close()
        self.rcsocket.close()


class AbstractCommander(object):

    """
    Abstraction of a FIPER console.
    Commands should be single words, but an arbitrary number of arguments
    may be supplied, seperated by a space. Because of this, the
    signature of the functions (the dictionary values) is recommended
    to be (*arg) for functions and static methods or (self, *arg)
    in case of bound object/class methods.
    A help command is supplied by default.
    Help can be called on a command, in which case the docstring of
    the appropriate function will be printed.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, master_name, status_tag="", commands_dict=None, **commands):
        """
        :param master_name: needed to build the console prompt
        :param status_tag: also for the console prompt
        :param commands_dict: commands as a string: callable mapping
        :param commands: commands can also be added as kwargs.
        """
        super(AbstractCommander, self).__init__()
        if not commands and not commands_dict:
            print("ABS_COMMANDER no command specified!")
            commands_dict = {} if commands_dict is None else commands_dict
        self.master_name = master_name
        self.status_tag = status_tag
        self.commands = {}
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
                      .format(cmd, E))
        self.running = False

        self.commands["shutdown"](*args)
        print("ABS_COMMANDER Exiting...")

    @abc.abstractmethod
    def read_cmd(self):
        raise NotImplementedError

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


class AbstractListener(object):

    """
    Abstract base class for an entity which acts like a server,
    eg. client in DirectConnection and FleetHandler server.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, myIP):
        self.mlistener = srvsock(myIP, "messaging", timeout=3)
        self.dlistener = srvsock(myIP, "stream")
        self.rclistener = srvsock(myIP, "rc", timeout=1)
        self.running = False

    @abc.abstractmethod
    def callback(self, msock):
        raise NotImplementedError

    def mainloop(self):
        """
        Unmanaged run for e.g. one-time connection bootstrapping
        """
        print("ABS_LISTENER: online")
        self.running = True
        while self.running:
            try:
                conn, addr = self.mlistener.accept()
            except socket.timeout:
                pass
            else:
                print("ABS_LISTENER: received connection from {}:{}"
                      .format(*addr))
                self.callback(conn)
        print("ABS_LISTENER: Exiting...")

    def teardown(self, sleep=2):
        self.running = False
        time.sleep(sleep)
        self.mlistener.close()
        self.dlistener.close()
        self.rclistener.close()

    def __del__(self):
        if self.running:
            self.teardown(2)
