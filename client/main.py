"""
BUG / HIaNYZo FEATURE REPORT:
- child ablak megnyitasa utan melleklikkeles eseten a focus elveszik es az enter / escape leutes hatastalan
- child ablak megnyitasa utan main menu gombok nem tunnek el
- zene hianyzik
- hangeffektek hianyzanak
"""


import wx
import os
import sys
import time
from wx import media

class MainFrame(wx.Frame):

	def __init__(self):
		wx.Frame.__init__(self, None, title='FIPER')
		# Get screen parameters
		resolution = wx.DisplaySize()
		self.width = resolution[0] 
		self.height = resolution[1]
		# Set App to FullScreen and get focus
		self.ShowFullScreen(True)
		# Set Background color black
		self.SetBackgroundColour('black')
		# Erase background from designated areas by DC ( for the buttons )
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.set_background)
		#
		# self.music()
		# self.Bind('<Escape>', self.quit_window(wx.EVT_BUTTON) )
		# Place buttons on background
		self.place_buttons() 
		# Set Custom Cursor Image 
		self.set_cursor()
		
		self.Bind(wx.EVT_SET_FOCUS, self.push_back_focus)
		
		# Show Application ( Grab Focus )
		self.Show()

		
	def set_background(self, event): 
		# Setting up Background with Transparency and ClippingRegion
		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		dc = event.GetDC()
		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRegionAsRegion()
		dc.Clear()
		# Image sources
		background_image = wx.Image('image\\menu\\bgnd.jpg').ConvertToBitmap()
		fiper_logo = wx.Image('image\\menu\\fiper_logo.png').ConvertToBitmap()
		# Scale and set textures
		self.background_bitmap = self.scale_bitmap(background_image, self.width, self.height)
		dc.DrawBitmap(self.background_bitmap, 0, 0, True)
		self.fiper_logo = self.scale_bitmap(fiper_logo, self.width*0.4, self.height*0.3)
		dc.DrawBitmap(self.fiper_logo, 40, -10, False)

		font = wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
		dc.SetFont(font)
		dc.SetTextForeground('white')
		dc.DrawText('Version: Pre-Alpha', self.width*0.005, self.height*0.97)
		dc.DrawText('Contact: GAL.MATEO @ GMAIL.COM', self.width*0.77, self.height*0.97)
		
	def scale_bitmap(self, bitmap, width, height):
		# This method scales a bitmap for a desired size
		image = wx.ImageFromBitmap(bitmap)
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		result = wx.BitmapFromImage(image)
		return result	
		
 	def set_cursor(self):
		# Custom cursor for the application
		cursor_path = ('image\\menu\\cursor.ico')
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)	
		
	def define_button_textures(self):
		self.connect_skin = wx.Bitmap('image\\menu\\buttons\\btn0.png')
		self.connect_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn0_hover.png')
		self.connect_skin_click = wx.Bitmap('image\\menu\\buttons\\btn0_click.png')
		
		self.options_skin = wx.Bitmap('image\\menu\\buttons\\btn1.png')
		self.options_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn1_hover.png')
		self.options_skin_click = wx.Bitmap('image\\menu\\buttons\\btn1_click.png')
		
		self.quit_skin = wx.Bitmap('image\\menu\\buttons\\btn2.png')
		self.quit_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn2_hover.png')
		self.quit_skin_click = wx.Bitmap('image\\menu\\buttons\\btn2_click.png')
		
		self.ok_skin = wx.Bitmap('image\\menu\\buttons\\btn3.png')
		self.ok_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn3_hover.png')
		self.ok_skin_click = wx.Bitmap('image\\menu\\buttons\\btn3_click.png')
		
		self.cancel_skin = wx.Bitmap('image\\menu\\buttons\\btn4.png')
		self.cancel_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn4_hover.png')
		self.cancel_skin_click = wx.Bitmap('image\\menu\\buttons\\btn4_click.png')
		
	def place_buttons(self):
		self.define_button_textures()
	
		# Place buttons on the background and define the behaviour of them 

		self.connect_button = wx.BitmapButton(self, -1, self.connect_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.3)), 
													size=(510,130))
		self.connect_button.SetBitmapHover(self.connect_skin_hover)
		self.connect_button.SetBitmapSelected(self.connect_skin_click)
		self.connect_button.Bind(wx.EVT_BUTTON, self.connect_window)
		#
		self.options_button = wx.BitmapButton(self, -1, self.options_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.5)), 
													size=(510,130))
		self.options_button.SetBitmapHover(self.options_skin_hover)
		self.options_button.SetBitmapSelected(self.options_skin_click)
		self.options_button.Bind(wx.EVT_BUTTON, self.options_window)
		#
		self.quit_button = wx.BitmapButton(self, -1, self.quit_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.7)), 
													size=(510,130))
		self.quit_button.SetBitmapHover(self.quit_skin_hover)
		self.quit_button.SetBitmapSelected(self.quit_skin_click)
		self.quit_button.Bind(wx.EVT_BUTTON, self.quit_window)
		
	def hide_buttons(self, event):
		
		self.connect_button.Destroy()
		self.connect_button.Hide()
		self.set_background()
		self.Update()
		self.connect_button.Update()
	
	def initiate_connection(self, event):
		print 'connected!'
		
		# FADE OUT 
		tp = 200 
		while(1):
			self.connect_window.SetTransparent(tp)
			time.sleep(.01)
			tp -= 10 
			self.connect_window.SetBackgroundColour((30,30,30))
			# self.SetBackgroundColour('#00aeef')
			# Keep Cursor Shape for new Frame 
			self.set_cursor()
			self.connect_window.Show()
			if ( tp == 0 ): break # Max transparency
		
		self.connect_window.Close()
		
	def connect_window(self, event):
		x_pos = (self.width * 0.025)
		y_pos = (self.height * 0.025)
		width = (self.width * 0.95)
		height = (self.height * 0.95)
		self.connect_window = NewFrame(' C O N N E C T ', width, height, x_pos, y_pos)
		
		self.connect_window.Bind( wx.EVT_KILL_FOCUS, self.connect_lost_focus )
		
		connect_list = wx.ListCtrl(	self.connect_window, size=(width*0.5,height*0.5), 
							pos=(width*0.05,height*0.4),style=wx.TE_MULTILINE )
		connect_list.SetBackgroundColour((0,0,0))
		
		"""
		dc = wx.ScreenDC() 
		dc.DrawText('Hello transparent window',width*0.7, height*0.1)
		"""
		
		"""
		list_file = 'connection.dat'
		with open(list_file) as file:
		"""
		
		cell_width = 150
		connect_list.InsertColumn(0, 'CAR NAME', width=cell_width)
		connect_list.InsertColumn(1, 'IP ADDRESS', width=cell_width)
		connect_list.InsertColumn(2, 'AVAILABLE', width=cell_width)
		connect_list.InsertColumn(3, 'PING', width=cell_width)
		connect_list.SetTextColour('white')
		
		row_index = 0
		connect_list.InsertStringItem(row_index, 'OpenRC Truggy')
		connect_list.SetStringItem(row_index, 1, '192.168.1.11')
		connect_list.SetStringItem(row_index, 2, 'YES')
		connect_list.SetStringItem(row_index, 3, '66')
		
		row_index = 1
		connect_list.InsertStringItem(row_index, 'Internet Exploder')
		connect_list.SetStringItem(row_index, 1, '192.168.1.14')
		connect_list.SetStringItem(row_index, 2, 'NO')
		connect_list.SetStringItem(row_index, 3, '0')

		row_index = 2
		connect_list.InsertStringItem(row_index, 'ScrotumCutter')
		connect_list.SetStringItem(row_index, 1, '192.168.0.21')
		connect_list.SetStringItem(row_index, 2, 'NO')
		connect_list.SetStringItem(row_index, 3, '30')

		ok_button_x = width * 0.8
		ok_button_y = height * 0.82
		ok_button = wx.BitmapButton(	self.connect_window, -1, self.ok_skin, 
											pos=(ok_button_x,ok_button_y), 
											size=(260,130)					)
		ok_button.SetBitmapHover(self.ok_skin_hover)
		ok_button.SetBitmapSelected(self.ok_skin_click)
		ok_button.Bind(wx.EVT_BUTTON, self.initiate_connection)
		
		cancel_button = wx.BitmapButton(	self.connect_window, -1, self.cancel_skin, 
												pos=(ok_button_x-300,ok_button_y), 
												size=(260,130)						)
		cancel_button.SetBitmapHover(self.cancel_skin_hover)
		cancel_button.SetBitmapSelected(self.cancel_skin_click)
		
	def options_window(self, event):
		x_pos = (self.width * 0.025)
		y_pos = (self.height * 0.025)
		width = (self.width * 0.95)
		height = (self.height * 0.95)
		self.options_window = NewFrame(' O P T I O N S ', width, height, x_pos, y_pos)
		
		# self.options_window.Bind( wx.EVT_KILL_FOCUS, self.options_lost_focus )
		
		ok_button_x = width * 0.8
		ok_button_y = height * 0.82
		ok_button = wx.BitmapButton(	self.options_window, -1, self.ok_skin, 
										pos=(ok_button_x,ok_button_y), 
										size=(260,130)					)
		ok_button.SetBitmapHover(self.ok_skin_hover)
		ok_button.SetBitmapSelected(self.ok_skin_click)
		
		
		cancel_button = wx.BitmapButton(	self.options_window, -1, self.cancel_skin, 
											pos=(ok_button_x-300,ok_button_y), 
											size=(260,130)						)
		cancel_button.SetBitmapHover(self.cancel_skin_hover)
		cancel_button.SetBitmapSelected(self.cancel_skin_click)
		
	def quit_window(self, event):
		x_pos = (self.width * 0.1)
		y_pos = (self.height * 0.3)
		width = (self.width * 0.5)
		height = (self.height * 0.5)
		
		
		self.quit_window = NewFrame(' Q U I T ', width, height, x_pos, y_pos)
		
		ok_button_x = width * 0.63
		ok_button_y = height * 0.6
		ok_button = wx.BitmapButton(	self.quit_window, -1, self.ok_skin, 
										pos=(ok_button_x,ok_button_y), 
										size=(260,130)					)
		ok_button.SetBitmapHover(self.ok_skin_hover)
		ok_button.SetBitmapSelected(self.ok_skin_click)
		ok_button.Bind(wx.EVT_BUTTON, self.exit)
		
		cancel_button = wx.BitmapButton(	self.quit_window, -1, self.cancel_skin, 
											pos=(ok_button_x-500,ok_button_y), 
											size=(260,130)						)
		cancel_button.SetBitmapHover(self.cancel_skin_hover)
		cancel_button.SetBitmapSelected(self.cancel_skin_click)
		
		
		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		dc = wx.ClientDC(self.quit_window)
		rect = self.GetUpdateRegion().GetBox()

		dc.Clear()

		font = wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
		dc.SetFont(font)
		dc.SetTextForeground('white')
		dc.DrawText('Oh, really?!', width*0.34, height*0.3)
	
	def push_back_focus(self, event):
		if ( NewFrame.instance_counter == 1 ):
			wx.Frame.SetFocus(self.quit_window)
	
	def quit_lost_focus(self, event):
		self.quit_window.SetFocus()
		
	def options_lost_focus(self, event):
		wx.Frame.SetFocus(self.options_window)
		
	def connect_lost_focus(self, event):
		wx.Frame.SetFocus(self.connect_window)
			
	def key_stroke_callback(self, event):
		self.quit_window(wx.EVT_BUTTON)
			
	def devastation(self, return_value):
		sys.exit(return_value)
			
	# def music(self):
		# self.music = wx.Sound('audio\\music\\carpenter_brut.wav')
		# if self.music.IsOk():
			# self.music.Play(wx.SOUND_ASYNC)
		# else:
			# print "Missing or invalid sound file", "Error"
			
	def music(self):
		music_file = 'audio\\music\\carpenter_brut.wav'
		self.mediaPlayer = wx.media.MediaCtrl(self,1)
		self.mediaPlayer.Load(music_file)
		self.mediaPlayer.Play()
		
		"""
		
		https://www.blog.pythonlibrary.org/2010/04/20/wxpython-creating-a-simple-mp3-player/
		
		"""

	def exit(self, event):
		sys.exit(0)
	
		
class NewFrame(wx.Frame):
	instance_counter = 0
	def __init__(self, title, width, height, x, y):
		
		# Counting the amound of instances to avoid creating infinite number of new frames 
		self.__class__.instance_counter += 1 
		if ( self.__class__.instance_counter > 1 ):
			self.Destroy()
			
		# Custom frame-look
		style = ( 	wx.CLIP_CHILDREN | wx.STAY_ON_TOP | 
					wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title=title, style = style)
		
		# Set Position and Size of new frame
		self.SetPosition((x,y))
		self.SetSize((width,height))
		
		# Make new frame transparent, black, and fade in
		tp = 0
		while(1):
			self.SetTransparent(tp)
			time.sleep(.01)
			tp += 10 
			self.SetBackgroundColour((30,30,30))
			# self.SetBackgroundColour('#00aeef')
			# Keep Cursor Shape for new Frame 
			self.set_cursor()
			self.Show()
			if ( tp == 200 ): break # Max transparency
			
		self.Bind(wx.EVT_CHAR_HOOK, self.key_stroke_callback)	
		# self.Bind(wx.EVT_CLOSE, self.hide_frame)
		
		
		w, h = width*0.3, 30
		bmp = wx.EmptyBitmap(w, h)
		dc = wx.MemoryDC()
		dc.SelectObject(bmp)
		dc.Clear()
		text = title
		tw, th = dc.GetTextExtent(text)
		font = wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
		dc.SetFont(font)
		dc.DrawText(text, (w-tw)/2,  (h-th)/2)
		dc.SelectObject(wx.NullBitmap)
		wx.StaticBitmap(self, -1, bmp)

	def set_cursor(self):
		cursor_path = ('image\\menu\\cursor.ico')
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 0, 0)
		self.SetCursor(cursor)

	def key_stroke_callback(self, event):
		if (event.GetKeyCode() == wx.WXK_ESCAPE):
			# FADE OUT 
			tp = 200
			while(1):
				self.SetTransparent(tp)
				time.sleep(.01)
				tp -= 10 
				self.SetBackgroundColour((30,30,30))
				# self.SetBackgroundColour('#00aeef')
				# Keep Cursor Shape for new Frame 
				self.set_cursor()
				self.Show()
				if ( tp == 0 ): break # Max transparency
			self.__class__.instance_counter = 0 
			self.Close()
			
		if (event.GetKeyCode() == wx.WXK_RETURN):
			sys.exit(0)
		event.Skip() 

	def input(self):
		print 'Input has been given.'

	def suicide(self, event):
		self.Hide()
	
	def hide_frame(self):
		self.Hide()
	
	def ignore_event(self, event):
		pass 
	
class Main(wx.App):
   
    def __init__(self):
		wx.App.__init__(self)
		dlg = MainFrame()
		dlg.Show()

if __name__ == "__main__":
    app = Main()
    app.MainLoop()
