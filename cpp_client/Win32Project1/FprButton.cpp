#include "FprButton.h"

FprButton::FprButton(wxWindow* parent, int ID, const wxString& title, const wxPoint& pos, const wxSize& size)
	: wxFrame(parent, ID, title, pos, size, wxCLIP_CHILDREN | wxSTAY_ON_TOP | wxFRAME_NO_TASKBAR | wxNO_BORDER | wxFRAME_SHAPED )
		//| wxTRANSPARENT_WINDOW)
{
	int	tp = 0;

		

	/*

	SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO, 0, 0));
	this->Show();
	wxClientDC dc(this);
	wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
	dc.SetFont(font);
	dc.SetTextForeground("black");
	dc.DrawText("Version: Pre-Alpha", 0, 0);*/
}

void FprButton::OnPaint(wxPaintEvent & evt)
{
	wxPaintDC dc(this);
	wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
	dc.SetFont(font);
	dc.SetTextForeground("black");
	dc.DrawText("Version: Pre-Alpha",0, 0);
	this->SetTransparent(0);
}