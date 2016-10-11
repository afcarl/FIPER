import sys
from Tkinter import *
from winsound import *
from PIL import ImageTk, Image
import tkFont
from threading import Thread
import pyglet
import time
from random import randint

window = Tk()

################################### MUSIC PLAYER ################################

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
	
################################### QUIR PROMPT ##################################	

def close_quit_prompt():
	
	PlaySound('audio\\sfx\\button.wav', SND_ASYNC ) 
	window.quit.destroy() 
	place_menu_buttons()
	
def quit_prompt():
	
	hide_menu_buttons()
	window.quit = Toplevel(window)
	
	window.quit.focus_force()
	window.quit.grab_set()
	
	window.quit.overrideredirect(True)
	window.quit.attributes('-alpha',0.7)
	window.quit.geometry('600x400+600+300')
	window.quit.configure(background='black')
	
	im_OK = Image.open('image\\menu\\ok_button.png')	
	ok_button_image = ImageTk.PhotoImage(im_OK)
	window.quit.yes_button = Button(window.quit, image=ok_button_image, command=exit_app )
	window.quit.yes_button.place(relx=0.62, rely=0.7, height=50, width=150)
	
	im_CANCEL = Image.open('image\\menu\\cancel_button.png')	
	cancel_button_image = ImageTk.PhotoImage(im_CANCEL)
	window.quit.no_button = Button(window.quit, image=cancel_button_image, command=close_quit_prompt)
	window.quit.no_button.place(relx=0.15, rely=0.7, height=50, width=150)
	
	window.quit.bind("<Escape>", lambda e: ( window.quit.destroy(), place_menu_buttons() )  )
	window.quit.bind("<Return>", lambda e: exit_app()  )
	
	customFont = tkFont.Font(family="Helvetica", size=30, weight=tkFont.BOLD)
	window.quit.text = Label(window.quit, text='ARE YOU SURE?', fg='red',bg ='black', font=customFont )
	window.quit.text.place(relx=0.25, rely=0.3)
	
	
	PlaySound('audio\\sfx\\button.wav', SND_ASYNC ) 
	#exit_app()
	
	window.quit.mainloop()
	
################################## CONNECT WINDOW ################################x
	
def close_connect_window():

	window.connect.destroy()
	place_menu_buttons()
	
def ok_connect_window():

	PlaySound('audio\\sfx\\button.wav', SND_ASYNC)
	window.connect.destroy()
	place_menu_buttons()
	
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
	window.connect.bind("<Return>", lambda e: ok_connect_window() ) # quit with escape button
	
	im_OK = Image.open('image\\menu\\ok_button.png')	
	ok_button_image = ImageTk.PhotoImage(im_OK)
	button_ok = Button(window.connect, image=ok_button_image, command=ok_connect_window )
	button_ok.place(relx=0.85, rely=0.9, height=50, width=150)
	
	window.connect.mainloop()
	
#################################### OPTIONS WINDOW #############################	

def close_options_window():

	window.options.destroy()
	place_menu_buttons()
	
def ok_options_window():

	PlaySound('audio\\sfx\\button.wav', SND_ASYNC)
	window.options.destroy()
	place_menu_buttons()
	
def options_window():

	hide_menu_buttons()
	
	window.options = Toplevel(window)
	window.options.focus_force()
	window.options.grab_set()
	window.options.overrideredirect(True)
	window.options.attributes('-alpha',0.7)
	window.options.geometry("1720x880+100+100")
	window.options.configure(background='black')
	window.options.bind("<Escape>", lambda x: close_options_window() ) # quit with escape button
	window.options.bind("<Return>", lambda x: ok_options_window() ) # quit with escape button
	
	im_OK = Image.open('image\\menu\\ok_button.png')	
	ok_button_image = ImageTk.PhotoImage(im_OK)
	button_ok = Button(window.options, image=ok_button_image, command = ok_options_window)
	button_ok.place(relx=0.85, rely=0.9, height=50, width=150)
	
	window.options.mainloop()

###################################### MAIN WINDOW ##############################	

def exit_app():

	pyglet.app.exit() 
	window.destroy()
	
def place_menu_buttons():

	button_connect.place(relx=0.7, rely=0.3, height=100, width=450)
	button_options.place(relx=0.7, rely=0.45, height=100, width=450)
	button_exit.place(relx=0.7, rely=0.6, height=100, width=450)

def hide_menu_buttons():

	button_connect.place_forget()
	button_options.place_forget()
	button_exit.place_forget()


screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()


background_image = Image.open('image\\menu\\background.jpg')
tkimage = ImageTk.PhotoImage(background_image)
Label(window,image = tkimage).pack()
window.iconbitmap('image\\icon.ico')
window.title('FIPER')
window.attributes('-fullscreen', True)
#window.bind('<Escape>',lambda e: quit_prompt() )
#window.configure(background='grey') # set background color	


button_connect = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC), connect_window() ) 
im1 = Image.open('image\\menu\\button1.png')
button_connect_image = ImageTk.PhotoImage(im1)
button_connect = Button(window, image=button_connect_image, cursor='cross', command=button_connect)


button_options = lambda: ( PlaySound('audio\\sfx\\button.wav', SND_ASYNC ), options_window() ) 
im2 = Image.open('image\\menu\\button2.png')
button_options_image = ImageTk.PhotoImage(im2)
button_options = Button(window, image=button_options_image, cursor='cross', command=button_options)


im3 = Image.open('image\\menu\\button3.png')
button_exit_image = ImageTk.PhotoImage(im3)
button_exit = Button(window, image=button_exit_image, cursor='cross', command=quit_prompt)


play_music()
place_menu_buttons()

window.mainloop()
