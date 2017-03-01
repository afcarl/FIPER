import wx

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
		# Set Custom Cursor Image 
		self.set_cursor()
		# Place buttons on background
		self.place_buttons()
		# Show Application ( Grab Focus )
		self.Show()
		
	def set_background(self, event): 
		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		dc = event.GetDC()
		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRegionAsRegion()
		dc.Clear()
		
		background_image = wx.Image('image\\menu\\bgnd.jpg').ConvertToBitmap()
		fiper_logo = wx.Image('image\\menu\\fiper_logo.png').ConvertToBitmap()
		
		background_bitmap = self.scale_bitmap(background_image, self.width, self.height)
		dc.DrawBitmap(background_bitmap, 0, 0, True)
		fiper_logo = self.scale_bitmap(fiper_logo, self.width*0.4, self.height*0.3)
		dc.DrawBitmap(fiper_logo, 40, -10, False)
		
	def scale_bitmap(self, bitmap, width, height):
		image = wx.ImageFromBitmap(bitmap)
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		result = wx.BitmapFromImage(image)
		return result	
		
	def set_cursor(self):
		cursor_path = ('image\\menu\\cursor.ico')
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)	
		
	def place_labels(self):
		self.label_email = label.transparent_text(self, 'hello', (200,200), 'green', 32)
		
	def place_buttons(self):
		self.connect_skin = wx.Bitmap('image\\menu\\buttons\\btn0.png')
		self.connect_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn0_hover.png')
		self.connect_skin_click = wx.Bitmap('image\\menu\\buttons\\btn0_click.png')
		self.connect_button = wx.BitmapButton(self, -1, self.connect_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.3)), 
													size=(510,130))
		self.connect_button.SetBitmapHover(self.connect_skin_hover)
		self.connect_button.SetBitmapSelected(self.connect_skin_click)
		self.connect_button.Bind(wx.EVT_BUTTON, self.connect_window)
		#
		self.options_skin = wx.Bitmap('image\\menu\\buttons\\btn1.png')
		self.options_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn1_hover.png')
		self.options_skin_click = wx.Bitmap('image\\menu\\buttons\\btn1_click.png')
		self.options_button = wx.BitmapButton(self, -1, self.options_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.5)), 
													size=(510,130))
		self.options_button.SetBitmapHover(self.options_skin_hover)
		self.options_button.SetBitmapSelected(self.options_skin_click)
		self.options_button.Bind(wx.EVT_BUTTON, self.options_window)
		#
		self.quit_skin = wx.Bitmap('image\\menu\\buttons\\btn2.png')
		self.quit_skin_hover = wx.Bitmap('image\\menu\\buttons\\btn2_hover.png')
		self.quit_skin_click = wx.Bitmap('image\\menu\\buttons\\btn2_click.png')
		self.quit_button = wx.BitmapButton(self, -1, self.quit_skin, 
													pos=(int(self.width*0.64),
													int(self.height*0.7)), 
													size=(510,130))
		self.quit_button.SetBitmapHover(self.quit_skin_hover)
		self.quit_button.SetBitmapSelected(self.quit_skin_click)
		self.quit_button.Bind(wx.EVT_BUTTON, self.quit_window)
		
	def connect_window(self, event):
		x_pos = (self.width * 0.025)
		y_pos = (self.height * 0.025)
		width = (self.width * 0.95)
		height = (self.height * 0.95)
		self.options_window = NewFrame('connect',width,height,x_pos,y_pos)
		
	def options_window(self, event):
		x_pos = (self.width * 0.025)
		y_pos = (self.height * 0.025)
		width = (self.width * 0.95)
		height = (self.height * 0.95)
		self.options_window = NewFrame('options',width,height,x_pos,y_pos)
		
	def quit_window(self, event):
		x_pos = (self.width * 0.35)
		y_pos = (self.height * 0.35)
		width = (self.width * 0.3)
		height = (self.height * 0.3)
		self.quit_window = NewFrame('quit', width, height, x_pos, y_pos)
		
		
class NewFrame(wx.Frame):
	
	def __init__(self, title, width, height, x, y):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title=title, style = style)
		# Set Position and Size of new frame
		self.SetPosition((x,y))
		self.SetSize((width,height))
		# Make new frame transparent, black,
		self.SetTransparent(200)
		self.SetBackgroundColour('Black')
		# Keep Cursor Shape for new Frame 
		self.set_cursor()
		self.Show()

	def set_cursor(self):
		cursor_path = ('image\\menu\\cursor.ico')
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)
			
		
	
class Main(wx.App):
   
    def __init__(self):
		wx.App.__init__(self)
		dlg = MainFrame()
		dlg.Show()

if __name__ == "__main__":
    app = Main()
    app.MainLoop()

