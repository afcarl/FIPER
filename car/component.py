from __future__ import print_function, absolute_import, unicode_literals

# stdlib imports
import os

# 3rd party imports
import cv2

# Project imports
from FIPER.generic.abstract import AbstractCommander
from FIPER.generic.util import CaptureDeviceMocker


class CaptureDevice(object):
    """
    Methods used for setting up a video capture device.
    """

    # noinspection PyArgumentList
    def __init__(self, dev=None, dummyfile=None):
        if dev is None:
            if not dummyfile:
                self.device = lambda: cv2.VideoCapture(0)
            elif not os.path.exists(dummyfile):
                self.device = CaptureDeviceMocker
            else:
                self.device = lambda: cv2.VideoCapture(dummyfile)
        else:
            self.device = dev

        self._eye = None

    def open(self):
        self._eye = self.device()

    def read(self):
        if self._eye is None:
            self.open()
        return self._eye.read()

    def close(self):
        self._eye.release()
        self._eye = None


class Commander(AbstractCommander):
    """
    Receives commands from the server
    """

    def __init__(self, messenger, **commands):
        super(Commander, self).__init__("Car", commands_dict=commands)
        self.messenger = messenger
        print("COMMANDER: online!")

    def read_cmd(self):
        m = self.messenger.recv(timeout=1)
        return m, None
