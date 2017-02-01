import wx
import label 
import time

class MainFrame(wx.Frame):

	def __init__(self):
		wx.Frame.__init__(self, None, title='Test')
		# Erase background from designated areas by DC ( for the buttons )
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.set_background)
		
		# Place labels on the background
		self.place_labels()
		
		# Place buttons on background
		self.place_buttons()
		

		# Set App to FullScreen and get focus
		self.ShowFullScreen(True)
		self.Show()
		
	def set_background(self, evt):
		self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
		dc = evt.GetDC()
		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRegionAsRegion()
		dc.Clear()
		bmp = wx.Bitmap("image\\menu\\bgnd.jpg")
		dc.DrawBitmap(bmp, 0, 0)

	def place_buttons(self):
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		
		connect_skin = wx.Bitmap('metal.jpg')
		self.connect_button = wx.BitmapButton(self, -1)

	def scale_bitmap(self, bitmap, width, height):
		image = wx.ImageFromBitmap(bitmap)
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		result = wx.BitmapFromImage(image)
		return result	

	def set_cursor(self):
		cursor_path = 'image\\menu\\cursor.ico'
		cursor = wx.Cursor(cursor_path, wx.BITMAP_TYPE_ICO, 6, 28)
		self.SetCursor(cursor)

	def place_labels(self):

		# Get Screen Resolution
		resolution = wx.DisplaySize()
		width = resolution[0] 
		height = resolution[1]
		
		# Define Labels
		version = label.TransparentText(self,'Release: Alpha', (10,height-30), 'white', 16)
		contact = label.TransparentText(self,'Contact:', (width-110,height-60), 'white', 16)
		email = label.TransparentText(self,'gal.mateo@gmail.com', (width-280,height-30), 'white', 16)
		
		# Place labels on the frame 
		email.Show()
		version.Show()
		contact.Show()
		
class Main(wx.App):
   
    def __init__(self):
		wx.App.__init__(self)
		dlg = MainFrame()
		dlg.Show()

if __name__ == "__main__":
    app = Main()
    app.MainLoop()
