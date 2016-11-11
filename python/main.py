#!/usr/bin/python
# main.py
import wx
import button 
import label 

class Frame(wx.Frame):
	
	def __init__(self, title):
		wx.Frame.__init__(self, parent=None, title=title, style=wx.TRANSPARENT_WINDOW)
		# Switch to FullScreen mode 
		self.ShowFullScreen(True)
		# Set Main Frame Background
		self.set_background()
		# Set Cursor Shape 
		self.set_cursor()
		# Place bottom labels 
		self.place_labels()
		
	def set_background(self):
		# Get Screen Resolution
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		# Background Image Source ( and bitmap conversion ) 
		image_file = 'image\\menu\\bgnd.jpg'
		background = wx.Image(image_file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		# Resize Background Image 
		background = self.scale_bitmap(background, width, height)
		# Set Background Image 
		self.background = wx.StaticBitmap(self, -1, background, (0, 0))	
		
	def scale_bitmap(self, bitmap, width, height):
		image = wx.ImageFromBitmap(bitmap)
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		result = wx.BitmapFromImage(image)
		return result	
		
	def set_cursor(self):
		cursor_path = 'image\\menu\\cursor.ico'
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)
	
	def place_buttons(self):
		image_file = 'image\\menu\\button.png'
		self.loc = wx.Bitmap(image_file)
		
		dc = wx.PaintDC(self)
		dc.SetBackground(wx.Brush("WHITE"))
		dc.DrawBitmap(self.loc, 0, 0, True)

	def place_labels(self):
		# Get Screen Resolution
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		
		# Define Labels
		version = label.TransparentText(self,'Release: Alpha', (10,height-30), 'white', 16)
		contact = label.TransparentText(self,'Contact:', (width-90,height-60), 'white', 16)
		email = label.TransparentText(self,'gal.mateo@gmail.com', (width-225,height-30), 'white', 16)
		
		# Place labels on the frame 
		email.Show()
		version.Show()
		contact.Show()
		
def main():					

	app = wx.App()  
	top = Frame("FIPER")
	top.Show()
	app.MainLoop()

main()
