import threading as thr

import cv2


class StreamDisplayer(thr.Thread):

    """
    Handles the cv2 displays for the car interfaces.
    """

    instances = 0

    def __init__(self, carint):
        self.interface = carint
        thr.Thread.__init__(self, name="Streamer-of-{}".format(carint.ID))
        self.running = True
        self.online = True
        self.start()
        StreamDisplayer.instances += 1

    def run(self):
        stream = self.interface.get_stream()
        for i, pic in enumerate(stream, start=1):
            # self.interface.out("\rRecieved {:>4} frames of shape {}"
            #                    .format(i, pic.shape), end="")
            cv2.imshow("{} Stream".format(self.interface.ID), pic)
            cv2.waitKey(1)
            if not self.running:
                break
        cv2.destroyWindow("{} Stream".format(self.interface.ID))
        self.online = False

    def __del__(self):
        StreamDisplayer.instances -= 1
