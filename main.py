#!/usr/bin/python
# main.py
import wx

class Frame(wx.Frame):
	
	def __init__(self, title):
		wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(350,200))
		self.configure_main_frame_geometry()
		# Set Cursor Shape 
		self.set_cursor()
		
	def configure_main_frame_geometry(self):
		# Set Window FullScreen
		self.ShowFullScreen(True)
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
	
class custom_button(wx.PyControl):

    def __init__(self, parent, id, bmp, text, **kwargs):
        wx.PyControl.__init__(self,parent, id, **kwargs)

        self.Bind(wx.EVT_LEFT_DOWN, self._onMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self._onMouseUp)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._onMouseLeave)
        self.Bind(wx.EVT_ENTER_WINDOW, self._onMouseEnter)
        self.Bind(wx.EVT_ERASE_BACKGROUND,self._onEraseBackground)
        self.Bind(wx.EVT_PAINT,self._onPaint)

        self._mouseIn = self._mouseDown = False

    def _on_mouse_enter(self, event):
        self._mouseIn = True

    def _on_mouse_leave(self, event):
        self._mouseIn = False

    def _on_mouse_down(self, event):
        self._mouseDown = True

    def _on_mouse_up(self, event):
        self._mouseDown = False
        self.sendButtonEvent()

    def send_button_event(self):
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.GetId())
        event.SetInt(0)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def _on_erase_blackground(self,event):
        # 
        pass

    def _onPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetFont(self.GetFont())
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        # draw whatever you want to draw
        # draw glossy bitmaps e.g. dc.DrawBitmap
        if self._mouseIn:
            pass# on mouserover may be draw different bitmap
        if self._mouseDown:
            pass # draw different image text
			
app = wx.App()  
top = Frame("FIPER")
top.Show()
app.MainLoop()


