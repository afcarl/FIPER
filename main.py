import sys
from Tkinter import *
from winsound import *
from PIL import ImageTk, Image
import tkFont

window = Tk()


im0 = Image.open('image\\background.jpg')
tkimage = ImageTk.PhotoImage(im0)
Label(window,image = tkimage).pack()

window.iconbitmap('image\\icon.ico')
window.title('FIPER')
window.attributes('-fullscreen', True)
window.configure(background='grey') # set background color
#window.bind("<Escape>", lambda e: e.widget.quit()) # quit with escape button

button_sound = lambda: PlaySound('audio\\push_button.wav', SND_NOSTOP, SND_ASYNC)
button_exit = lambda: 	( PlaySound('audio\\push_button.wav', SND_FILENAME), exit() ) 
PlaySound('audio\\menu.wav', SND_ASYNC)



im1 = Image.open('image\\button1.png')
button_connect_image = ImageTk.PhotoImage(im1)
button_connect = Button(window, image=button_connect_image, cursor='cross', command=button_sound)
button_connect.place(relx=0.7, rely=0.3, height=100, width=450)

im2 = Image.open('image\\button2.png')
button_host_image = ImageTk.PhotoImage(im2)
button_host = Button(window, image=button_host_image, cursor='cross', command=button_sound)
button_host.place(relx=0.7, rely=0.45, height=100, width=450)

im3 = Image.open('image\\button3.png')
button_exit_image = ImageTk.PhotoImage(im3)
button_exit = Button(window, image=button_exit_image, cursor='cross', command=button_exit)
button_exit.place(relx=0.7, rely=0.6, height=100, width=450)

window.mainloop()
