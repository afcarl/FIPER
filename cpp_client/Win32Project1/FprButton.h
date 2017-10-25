#pragma once
#include <wx/wx.h>

class FprButton : public wxFrame
{
public:

	FprButton(wxWindow* parent, int ID, const wxString& title, const wxPoint& pos, const wxSize& size);

private:

	void OnPaint(wxPaintEvent &evt);

	wxDECLARE_EVENT_TABLE();
};