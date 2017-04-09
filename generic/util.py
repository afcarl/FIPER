from __future__ import print_function, absolute_import, unicode_literals

from .routines import white_noise


DUMMY_FRAMESIZE = (480, 640, 3)  # = 921,600 B in uint8


class CaptureDeviceMocker(object):

    """
    Mocks the interface of cv2.VideoCapture,
    produces a white noise stream.
    """

    @staticmethod
    def read():
        return True, white_noise(DUMMY_FRAMESIZE)


class Table(object):

    def __init__(self, header, cell_widths):
        self.header = header
        self.widths = dict(zip(header, cell_widths))
        wd = self.widths
        self.headerrow = "|" + "|".join("{k:^{v}}".format(k=k, v=wd[k]) for k in header) + "|"
        self.separator = "+" + "+".join(("-" * wd[k] for k in header)) + "+"
        self.rowtemplate = "|" + "|".join("{}" * len(self.header)) + "|"
        self.data = []

    def add(self, *data):
        if len(data) != len(self.header):
            raise ValueError("Invalid number of data elements. Expected: {}"
                             .format(len(self.header)))
        self.data.extend([self.separator, self.rowtemplate.format(*data)])

    def get(self):
        if not self.data:
            return "Empty table"
        output = [self.headerrow, self.separator] + self.data + [self.separator]
        return "\n".join(output)
