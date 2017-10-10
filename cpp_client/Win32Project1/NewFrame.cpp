#include "NewFrame.h"

NewFrame::NewFrame(int ID, const wxString& title, const wxPoint& pos, const wxSize& size, wxWindow* parent)
	: wxFrame(parent, ID, title, pos, size, wxCLIP_CHILDREN | wxSTAY_ON_TOP |
		wxFRAME_NO_TASKBAR | wxNO_BORDER | wxFRAME_SHAPED)
{
	//static int instanceCounter =0;
	
	//++instanceCounter;
	// Make new frame transparent, black, and fade in

	this->parent = parent;
	this->SetFocus();
	int	tp = 0;
	while (tp < 200) // Max transparency
	{
		this->SetTransparent(tp);
		Sleep(10);
		tp += 10;
		this->SetBackgroundColour((30, 30, 30));

		// Keep Cursor Shape for new Frame
		SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO, 6, 28));
		this->Show();
		//this->Bind(wxEVT_CHAR_HOOK, &NewFrame::key_stroke_callback);

		ok_skin = new wxBitmap("image/menu/buttons/btn3.png", wxBITMAP_TYPE_PNG);
		ok_skin_hover = new wxBitmap("image/menu/buttons/btn3_hover.png", wxBITMAP_TYPE_PNG);
		ok_skin_click = new wxBitmap("image/menu/buttons/btn3_click.png", wxBITMAP_TYPE_PNG);

		cancel_skin = new wxBitmap("image/menu/buttons/btn4.png", wxBITMAP_TYPE_PNG);
		cancel_skin_hover = new wxBitmap("image/menu/buttons/btn4_hover.png", wxBITMAP_TYPE_PNG);
		cancel_skin_click = new wxBitmap("image/menu/buttons/btn4_click.png", wxBITMAP_TYPE_PNG);

	}
}
void NewFrame::key_stroke_callback(wxKeyEvent& event)
{
	if (event.GetKeyCode() == WXK_ESCAPE)
	{
		// FADE OUT
		int tp = 200;
		while(tp)
		{
			this->SetTransparent(tp);
			Sleep(10);
			tp -= 10;
			this->SetBackgroundColour((30, 30, 30));
			// Keep Cursor Shape for new Frame
			SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO, 6, 28));
			//this->instanceCounter = 0;
				
			//this->parent.show_buttons();
			if (event.GetKeyCode() == WXK_RETURN)
			{
				//sys.exit(0);
				//event.Skip();
			}
		}
		this->Close();
	}
}
void NewFrame::OnPaint(wxPaintEvent & evt)
{
	
	int width, height;
	this->GetSize(&width, &height);
	int ok_button_x = width * 0.79;
	int ok_button_y = height * 0.8;
	okButton = new wxBitmapButton(this, WINDOW_CONNECT, *ok_skin,
		 wxPoint(ok_button_x, ok_button_y), wxSize(260, 130));

	okButton->SetBitmapHover(*ok_skin_hover);
	okButton->SetBitmapSelected(*ok_skin_click);

	//ok_button.Bind(wxEVT_BUTTON, self.initiate_connection);

	//wxBitmapButton cancel_button = wx.BitmapButton(self.connect_window, -1, self.cancel_skin,
	//	pos = (ok_button_x - 300, ok_button_y),
	//	size = (260, 130));
	//cancel_button.SetBitmapHover(self.cancel_skin_hover);
	//cancel_button.SetBitmapSelected(self.cancel_skin_click);



	//this->SetFocus();
}

