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


