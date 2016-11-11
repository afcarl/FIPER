#!/usr/bin/python
# label.py
import wx


class TransparentText(wx.StaticText):

	def __init__(	self, parent, label, pos, font_color, font_size, 
					size=(800,800), id=wx.ID_ANY, style=wx.TRANSPARENT_WINDOW, 
					name='tpwindow'	):
		
		wx.StaticText.__init__(self, parent, id, label, pos, size, style, name)
		self.Bind(wx.EVT_PAINT, self.on_paint)
		self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
		self.Bind(wx.EVT_SIZE, self.on_size)
		self.font_color = font_color
		self.font_size = font_size
		
	def on_paint(self, event):
		bdc = wx.PaintDC(self)
		dc = wx.GCDC(bdc)
		font_face = wx.Font(self.font_size, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
		dc.SetFont(font_face)
		dc.SetTextForeground(self.font_color)
		dc.DrawText(self.GetLabel(), 0, 0)

	def on_size(self, event):
		self.Refresh()
		event.Skip()
		
		