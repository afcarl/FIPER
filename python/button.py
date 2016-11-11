#!/usr/bin/python
# button.py 
import wx 

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

    def _on_erase_background(self,event):
        # 
        pass

    def _on_paint(self, event):
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