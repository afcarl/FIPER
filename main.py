import sys
from Tkinter import *
from winsound import *
from PIL import ImageTk, Image
import tkFont
from threading import Thread
import pyglet
import time

window = Tk()


def player_config():
	player = pyglet.media.Player()
	music_file = pyglet.media.load('audio\\music\\track01.mp3')
	player.queue(music_file)
	player.play()
	pyglet.app.run()

def play_music():
	global sound_thread 
	sound_thread = Thread(target=player_config)
	sound_thread.start()
	
def exit_app():
	pyglet.app.exit() 
	window.destroy()

play_music()


background_image = Image.open('image\\menu\\background.jpg')
tkimage = ImageTk.PhotoImage(background_image)
Label(window,image = tkimage).pack()
window.iconbitmap('image\\icon.ico')
window.title('FIPER')
window.attributes('-fullscreen', True)
#window.configure(background='grey') # set background color
window.bind("<Escape>", lambda e: (e.widget.quit(), exit_app() )) # quit with escape button
	
button_connect = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC) ) 
button_options = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC ) ) 
button_exit = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC ), exit_app() ) 

im1 = Image.open('image\\menu\\button1.png')
button_connect_image = ImageTk.PhotoImage(im1)
button_connect = Button(window, image=button_connect_image, cursor='cross', command=button_connect)
button_connect.place(relx=0.7, rely=0.3, height=100, width=450)

im2 = Image.open('image\\menu\\button2.png')
button_host_image = ImageTk.PhotoImage(im2)
button_host = Button(window, image=button_host_image, cursor='cross', command=button_options)
button_host.place(relx=0.7, rely=0.45, height=100, width=450)

im3 = Image.open('image\\menu\\button3.png')
button_exit_image = ImageTk.PhotoImage(im3)
button_exit = Button(window, image=button_exit_image, cursor='cross', command=button_exit)
button_exit.place(relx=0.7, rely=0.6, height=100, width=450)



window.mainloop()
