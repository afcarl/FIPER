from __future__ import print_function, unicode_literals, absolute_import

import abc
import socket
import threading as thr
import time

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
            print("AbstractConsole: no commands specified!")
        self.master_name = master_name
        self.status_tag = status_tag
        self.commands = {}
        self.commands.update(commands_dict)
        self.commands.update(commands)
        if "help" not in self.commands:
            self.commands["help"] = self.help
        if "shutdown" not in commands:
            raise RuntimeError("Please provide a shutdown command!")
        self.running = True

    def help(self, *args):
        """Who helps the helpers?"""
        if not args:
            print("Available commands:", ", ".join(sorted(self.commands)))
        else:
            for arg in args:
                if arg not in self.commands:
                    print("No such command: [{}]".format(arg))
                else:
                    print("Docstring for [{}]: {}"
                          .format(arg, self.commands[arg].__doc__.replace("\n", " ")))

    @property
    def prompt(self):
        return " ".join((self.master_name, ("[{}]".format(self.status_tag)
                         if self.status_tag else ""), "> "))

    def run(self):
        """
        Server console main loop (and program main loop)
        """
        while self.running:
            cmd, args = self.read_cmd()
            if not cmd:
                continue
            elif cmd == "shutdown":
                break
            else:
                try:
                    self.commands[cmd](*args)
                except Exception as E:
                    print("CONSOLE: command [{}] caused an exception: {}"
                          .format(cmd, E.message))
                    print("CONSOLE: ignoring commad!")
        self.commands["shutdown"](*args)
        print("CONSOLE: exiting")

    def read_cmd(self):
        c = raw_input(self.prompt).split(" ")
        cmd = c[0].lower()
        if len(c) > 1:
            args = c[1:]
        else:
            args = ""
        return cmd, args

    def cmd_parser(self, cmd, args):
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

    def run(self):
        """
        Managed run, mainly intended to use in a separate thread
        """
        try:
            self.mainloop()
        except:
            raise
        finally:
            self.teardown()

    def mainloop(self):
        """
        Unmanaged run for e.g. one-time connection bootstrapping
        """
        self.running = True
        while self.running:
            try:
                conn, addr = self.msocket.accept()
            except socket.timeout:
                print("ABS_LISTENER: timeout!")
            else:
                print("ABS_LISTENER: Received connection from {}:{}"
                      .format(*addr))
                self.callback(conn)

    def teardown(self, sleep=2):
        print("AL: teardown")
        self.running = False
        time.sleep(sleep)
        self.msocket.close()
        self.dsocket.close()
        self.rcsocket.close()

    def __del__(self):
        print("AL: deconstructed :(")
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
        self.online = True
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
        self.online = False

    def teardown(self, sleep=1):
        self.running = False
        time.sleep(sleep)

    def __del__(self):
        if self.running or self.online:
            self.teardown(sleep=1)
