from __future__ import print_function, unicode_literals, absolute_import

import abc
import time
import socket
import subprocess
import threading as thr

from .routines import srvsock


class Console(object):
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

    def __init__(self, master_name, status_tag="", commands_dict={}, **commands):
        """
        
        :param master_name: needed to build the console prompt
        :param status_tag: also for the console prompt
        :param commands_dict: commands as a string: callable mapping
        :param commands: commands can also be added as kwargs.
        """
        super(Console, self).__init__()
        if not commands and not commands_dict:
            print("ABS_CONSOLE: no command specified!")
        self.master_name = master_name
        self.status_tag = status_tag
        self.commands = {}
        self.commands.update(commands_dict)
        self.commands.update(commands)

        if "help" not in self.commands:
            self.commands["help"] = self.help
        if "clear" not in self.commands:
            self.commands["clear"] = lambda: subprocess.call("clear", shell=True)
        if "shutdown" not in commands:
            raise RuntimeError("Please provide a shutdown command!")
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
        return " ".join((self.master_name, ("[{}]".format(self.status_tag)
                                            if self.status_tag else ""), "> "))

    def run(self):
        """
        Server console main loop (and program main loop)
        """
        print("CONSOLE: online")
        self.running = True
        while self.running:
            cmd, args = self._read_cmd()
            if not cmd:
                continue
            elif cmd == "shutdown":
                break
            else:
                self.commands[cmd](*args)
                # except Exception as E:
                #     print("CONSOLE: command [{}] raised: {}"
                #           .format(cmd, E.message))
        self.commands["shutdown"](*args)
        print("CONSOLE: Exiting...")

    def _read_cmd(self):
        c = raw_input(self.prompt).split(" ")
        cmd = c[0].lower()
        if len(c) > 1:
            args = c[1:]
        else:
            args = ""
        return cmd, args

    def _cmd_parser(self, cmd, args):
        if cmd[0] not in self.commands:
            print("CONSOLE: Unknown command:", cmd)
        else:
            self.commands[cmd](*args)


class AbstractListener(object):
    """
    Abstract base class for an entity which acts like a server,
    eg. client in DirectConnection and FleetHandler server.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, myIP, callback_on_connection):
        """
        Listens for entities on the local network.
        Incomming connections produce a connected socket,
        on which callback_on_connection is called, so
        callback_on_connection's signature should look like so:
        callback(msock), where msock will be the connected socket.
        """
        self.msocket = srvsock(myIP, "messaging", timeout=3)
        self.dsocket = srvsock(myIP, "stream")
        self.rcsocket = srvsock(myIP, "rc", timeout=1)
        self.running = False
        self.callback = callback_on_connection

    def mainloop(self):
        """
        Unmanaged run for e.g. one-time connection bootstrapping
        """
        print("ABS_LISTENER: online")
        self.running = True
        while self.running:
            try:
                conn, addr = self.msocket.accept()
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
        self.msocket.close()
        self.dsocket.close()
        self.rcsocket.close()

    def __del__(self):
        if self.running:
            self.teardown(2)


class StreamDisplayer(thr.Thread):
    """
    Displays the video streams of cars.
    Instantiating this class instantly launches it
    in a separate thread.
    """

    # TODO: handle the cv2 display's close (X) button...

    def __init__(self, carint):
        """
        :param carint: CarInterface instance 
        """
        self.interface = carint
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = True
        print("STREAM_DISPLAYER: online")
        self.start()

    def run(self):
        """
        Displays the remote car's stream with cv2.imshow()
        """
        import cv2
        stream = self.interface.framestream()
        for i, pic in enumerate(stream, start=1):
            # self.interface.out("\rRecieved {:>4} frames of shape {}"
            #                    .format(i, pic.shape), end="")
            cv2.imshow("{} Stream".format(self.interface.ID), pic)
            cv2.waitKey(1)
            if not self.running:
                break
        cv2.destroyWindow("{} Stream".format(self.interface.ID))
        print("STREAM_DISPLAYER: Exiting...")

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running:
            self.teardown(sleep=1)
