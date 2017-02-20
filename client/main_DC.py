import wx


class MainFrame(wx.Frame):

	def __init__(self):
		wx.Frame.__init__(self, None, title='Test')
		# Set App to FullScreen and get focus
		self.ShowFullScreen(1)
		# Erase background from designated areas by DC ( for the buttons )
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.set_background)
		# Set Custom Cursor Image 
		self.set_cursor()
		# Place buttons on background
		self.place_buttons()
		
		self.place_labels()
		
		# Show Application ( Grab Focus )
		self.Show()
		
	def set_background(self, evt):
		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		dc = evt.GetDC()
		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRegionAsRegion()
		dc.Clear()
		bmp = wx.Bitmap('image\\menu\\bgnd.jpg')
		bitmap = self.scale_bitmap(bmp)
		dc.DrawBitmap(bitmap, 0, 0)

	def scale_bitmap(self, bitmap):
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]

		image = wx.ImageFromBitmap(bitmap)
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		result = wx.BitmapFromImage(image)
		return result	
		
	def set_cursor(self):
		cursor_path = ('image\\menu\\cursor.ico')
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)	
		
	def place_buttons(self):
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		
		connect_skin = wx.Bitmap('image\\menu\\buttons\\btn0.png')
		connect_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn0_hover.png')
		connect_skin_click = wx.Bitmap('image\\menu\\buttons\\btn0_click.png')
		connect_button = wx.BitmapButton(self, -1, connect_skin, pos=(int(width*0.65),int(height*0.3)), size=(510,130))
		connect_button.SetBitmapHover(connect_skin_hover)
		connect_button.SetBitmapSelected(connect_skin_click)
	
		options_skin = wx.Bitmap('image\\menu\\buttons\\btn1.png')
		options_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn1_hover.png')
		options_skin_click = wx.Bitmap('image\\menu\\buttons\\btn1_click.png')
		options_button = wx.BitmapButton(self, -1, options_skin, pos=(int(width*0.65),int(height*0.5)), size=(510,130))
		options_button.SetBitmapHover(options_skin_hover)
		options_button.SetBitmapSelected(options_skin_click)
		
		quit_skin = wx.Bitmap('image\\menu\\buttons\\btn2.png')
		quit_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn2_hover.png')
		quit_skin_click = wx.Bitmap('image\\menu\\buttons\\btn2_click.png')
		quit_button = wx.BitmapButton(self, -1, quit_skin, pos=(int(width*0.65),int(height*0.7)), size=(510,130))
		quit_button.SetBitmapHover(quit_skin_hover)
		quit_button.SetBitmapSelected(quit_skin_click)
		self.Bind(wx.EVT_BUTTON, self.close_app, quit_button)
		
	def place_labels(self):
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		
	def close_app(self, event):
		self.Close(True)
		
class Main(wx.App):
   
    def __init__(self):
		wx.App.__init__(self)
		dlg = MainFrame()
		dlg.Show()

if __name__ == "__main__":
    app = Main()
    app.MainLoop()
