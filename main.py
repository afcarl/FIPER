import sys
from Tkinter import *
from winsound import *
from PIL import ImageTk, Image
import tkFont
from threading import Thread
import pyglet
import time
import win32api

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

def close_connect_window():
	window.connect.destroy()
	place_menu_buttons()

def close_options_window():
	window.options.destroy()
	place_menu_buttons()
	
def ok_connect_window():
	window.options.destroy()
	place_menu_buttons()
	
def ok_options_window():
	window.options.destroy()
	place_menu_buttons()

def quit_prompt():
	window.quit_prompt = Toplevel(window)
	window.quit_prompt.mainloop()
	
def connect_window():
	hide_menu_buttons()
	window.connect = Toplevel(window)
	window.connect.grab_set()
	window.connect.overrideredirect(True)
	window.connect.attributes('-alpha',0.7)
	window.connect.geometry("1720x880+100+100")
	
	window.connect.configure(background='black')
	window.connect.focus_force()
	window.connect.bind("<Escape>", lambda e: close_connect_window() ) # quit with escape button
	
	im_OK = Image.open('image\\menu\\ok_button.png')	
	ok_button_image = ImageTk.PhotoImage(im_OK)
	button_ok = Button(window.connect, image=ok_button_image, command=close_connect_window )
	button_ok.place(relx=0.85, rely=0.9, height=50, width=150)
	
	window.connect.mainloop()
	
def options_window():
	hide_menu_buttons()
	window.options = Toplevel(window)
	window.options.focus_force()
	window.options.grab_set()
	window.options.overrideredirect(True)
	window.options.attributes('-alpha',0.7)
	window.options.geometry("1720x880+100+100")
	window.options.configure(background='black')
	window.options.bind("<Escape>", lambda e: ( window.options.destroy(), place_menu_buttons() )) # quit with escape button
	
	im_OK = Image.open('image\\menu\\ok_button.png')	
	ok_button_image = ImageTk.PhotoImage(im_OK)
	button_ok = Button(window.options, image=ok_button_image, command = close_options_window)
	button_ok.place(relx=0.85, rely=0.9, height=50, width=150)
	
	window.options.mainloop()

def place_menu_buttons():
	button_connect.place(relx=0.7, rely=0.3, height=100, width=450)
	button_options.place(relx=0.7, rely=0.45, height=100, width=450)
	button_exit.place(relx=0.7, rely=0.6, height=100, width=450)

def hide_menu_buttons():
	button_connect.place_forget()
	button_options.place_forget()
	button_exit.place_forget()

button_connect = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC), connect_window() ) 
button_options = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC ), options_window() ) 
button_exit = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC ), exit_app() ) 


screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()


background_image = Image.open('image\\menu\\background.jpg')
tkimage = ImageTk.PhotoImage(background_image)
Label(window,image = tkimage).pack()
window.iconbitmap('image\\icon.ico')
window.title('FIPER')
window.attributes('-fullscreen', True)
#window.configure(background='grey') # set background color	


im1 = Image.open('image\\menu\\button1.png')
button_connect_image = ImageTk.PhotoImage(im1)
button_connect = Button(window, image=button_connect_image, cursor='cross', command=button_connect)

im2 = Image.open('image\\menu\\button2.png')
button_options_image = ImageTk.PhotoImage(im2)
button_options = Button(window, image=button_options_image, cursor='cross', command=button_options)

im3 = Image.open('image\\menu\\button3.png')
button_exit_image = ImageTk.PhotoImage(im3)
button_exit = Button(window, image=button_exit_image, cursor='cross', command=button_exit)


play_music()
place_menu_buttons()

window.mainloop()
