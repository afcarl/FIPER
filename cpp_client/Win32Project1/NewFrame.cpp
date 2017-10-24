#include "NewFrame.h"

NewFrame::NewFrame(int ID, const wxString& title, const wxPoint& pos, const wxSize& size, wxWindow* parent)
	: wxFrame(parent, ID, title, pos, size, wxCLIP_CHILDREN | wxSTAY_ON_TOP |
		wxFRAME_NO_TASKBAR | wxNO_BORDER | wxFRAME_SHAPED), slider(nullptr), size(size)
{

	// Make new frame transparent, black, and fade in

	this->parent = parent;
	this->SetFocus();
	int	tp = 0;
//	slider = new wxSlider(this, SLIDER_VOLUME, 0, 0, 100, wxPoint(700*0.3, 30), wxSize(1000*0.5, 30));
	ok_skin = new wxBitmap("image/menu/buttons/btn3.png", wxBITMAP_TYPE_PNG);
	ok_skin_hover = new wxBitmap("image/menu/buttons/btn3_hover.png", wxBITMAP_TYPE_PNG);
	ok_skin_click = new wxBitmap("image/menu/buttons/btn3_click.png", wxBITMAP_TYPE_PNG);

	cancel_skin = new wxBitmap("image/menu/buttons/btn4.png", wxBITMAP_TYPE_PNG);
	cancel_skin_hover = new wxBitmap("image/menu/buttons/btn4_hover.png", wxBITMAP_TYPE_PNG);
	cancel_skin_click = new wxBitmap("image/menu/buttons/btn4_click.png", wxBITMAP_TYPE_PNG);

	while (tp < 200) // Max transparency
	{
		this->SetTransparent(tp);
		Sleep(10);
		tp += 10;
		this->SetBackgroundColour((30, 30, 30));

		// Keep Cursor Shape for new Frame
		SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO));
		this->Show();
		//this->Bind(wxEVT_CHAR_HOOK, &NewFrame::key_stroke_callback);



	}
}

void NewFrame::key_stroke_callback(wxKeyEvent& event)
{
	if (event.GetKeyCode() == WXK_ESCAPE)
	{
		// FADE OUT
		int tp = 200;
		while (tp)
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
		MainFrame* window = wxDynamicCast(parent, MainFrame);
		if (window != nullptr)
		{
			window->show_buttons();
		}
		else
		{
			wxMessageBox(wxT("Main is NULL"));
		}
		this->Destroy();
	}
}

void NewFrame::OnPaint(wxPaintEvent & evt)
{
	/*static int i = 0;
	std::string str = std::to_string(++i);
	wxString ws(str);
	wxMessageBox(ws);*/
	
	int width, height;
	this->GetSize(&width, &height);
	
	wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
	wxPaintDC dc(this);
	dc.SetFont(font);
	dc.SetTextForeground("GREY");
	dc.DrawText("VOLUME", 50, 30);
	slider = new wxSlider(this, SLIDER_VOLUME, 100, 0, 100, wxPoint(width*0.3 ,30), wxSize(width*0.5, 30), wxSL_HORIZONTAL | wxSL_AUTOTICKS);

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
void NewFrame::changeVolume(wxCommandEvent& evt)
{
	
}

void NewFrame::KillFocus(wxFocusEvent& evt)
{
	this->SetFocus();
}
