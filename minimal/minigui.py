from __future__ import print_function

import Tkinter as tk
from PIL import Image, ImageTk

from minimalclient import listen, framestream
from minimalgeneric import configparse


class Root(tk.Tk, object):

    def __init__(self):
        super(Root, self).__init__()
        self.cfg = configparse()
        self.title("FIPER Testing Environment")
        h, w, d = self.cfg["webcam_resolution"]
        self.canvas = tk.Canvas(self, width=w, height=h)
        self.canvas.pack()
        self.mconn, self.dconn = listen(self.cfg)
        self.image = None
        self.photo = None
        self.stream = framestream(self.dconn, self.cfg)
        self.after("idle", self.set_image)
        self.bind("<Key>", self.keypress)

    def keypress(self, event):
        print("Sending", event.char)
        self.mconn.sendall(event.char)

    def set_image(self):
        array = next(self.stream)
        self.image = Image.fromarray(array[:, :, ::-1], "RGB")
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.after(10, self.set_image)


if __name__ == '__main__':
    app = Root()
    app.mainloop()
