#pragma once
#include<wx/wx.h>
#include "ids.h"
#include "MainFrame.h"

class NewFrame : public wxFrame
{
public:
	NewFrame(int ID, const wxString& title, const wxPoint& pos, const wxSize& size, wxWindow* parent);

	wxBitmapButton* okButton;
	wxBitmapButton* cancelButton;
private:
	void OnPaint(wxPaintEvent & evt);
	wxWindow* parent;
	wxBitmap* ok_skin;
	wxBitmap* ok_skin_hover;
	wxBitmap* ok_skin_click;
	wxBitmap* cancel_skin;
	wxBitmap* cancel_skin_hover;
	wxBitmap* cancel_skin_click;
	void key_stroke_callback(wxKeyEvent& event);
		wxDECLARE_EVENT_TABLE();

};