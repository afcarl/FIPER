#include "NewFrame.h"

wxBEGIN_EVENT_TABLE(NewFrame, wxFrame)
EVT_PAINT(NewFrame::OnPaint)
EVT_KILL_FOCUS(NewFrame::KillFocus)
EVT_KEY_DOWN(NewFrame::key_stroke_callback)
EVT_SLIDER(SLIDER_VOLUME, NewFrame::changeVolume)
EVT_BUTTON(BUTTON_CANCEL, NewFrame::OnExit)

wxEND_EVENT_TABLE()


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
	this->SetFocus();
}

void NewFrame::FadeOut()
{
	int tp = 200;
	while (tp)
	{
		this->SetTransparent(tp);
		Sleep(10);
		tp -= 10;
		this->SetBackgroundColour((30, 30, 30));
		// Keep Cursor Shape for new Frame
		SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO));
	}
	MainFrame* window = wxDynamicCast(parent, MainFrame);
	if (window != nullptr)
	{
		window->show_buttons();
	}
	this->Destroy();
}

void NewFrame::key_stroke_callback(wxKeyEvent& event)
{
	if (event.GetKeyCode() == WXK_ESCAPE)
	{
		FadeOut();
	}
}

void NewFrame::OnExit(wxCommandEvent& evt)
{
	FadeOut();
}
void NewFrame::OnPaint(wxPaintEvent & evt)
{
	/*static int i = 0;
	std::string str = std::to_string(++i);
	wxString ws(str);
	wxMessageBox(ws);*/


	int width, height;
	this->GetSize(&width, &height);
	int okButtonId;
	int ok_button_x = width * 0.79;
	int ok_button_y = height * 0.8;
	wxSize ok_button_size(260, 130);
	wxSize cancel_button_size(260, 130);
	wxPaintDC dc(this);
	switch (this->GetId())
	{
		case WINDOW_OPTIONS:
		{
			okButtonId = BUTTON_OPTIONS_OK;
			wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
			dc.SetFont(font);
			dc.SetTextForeground("GREY");
			dc.DrawText("VOLUME", 50, 30);
			dc.DrawText("SFX", 50, 60);
			slider = new wxSlider(this, SLIDER_VOLUME, 10, 0, 10, wxPoint(width*0.3, 30), wxSize(width*0.5, 30), wxSL_HORIZONTAL | wxSL_AUTOTICKS);
			sliderSFX = new wxSlider(this, SLIDER_SFX, 10, 0, 10, wxPoint(width*0.3, 60), wxSize(width*0.5, 30), wxSL_HORIZONTAL | wxSL_AUTOTICKS);
			ok_button_x = width * 0.63;
			ok_button_y = height * 0.6;
			break;
		}
		case WINDOW_CONNECT:
		{
			okButtonId = BUTTON_CONNECT_OK;
			break;
		}
		
		case WINDOW_QUIT:
		{

			okButtonId = BUTTON_QUIT_OK;
			wxFont font(32, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
				dc.SetFont(font);
				dc.SetTextForeground("white");
				dc.DrawText("Oh, really?!", width*0.34, height*0.3);
				ok_button_x = width * 0.63;
				ok_button_y = height * 0.6;
				//ok_button_size = wxSize(115, 75);
				//cancel_button_size = wxSize(115, 75);
				break;
		}

	}

	okButton = new wxBitmapButton(this, okButtonId, *ok_skin,
		wxPoint(ok_button_x, ok_button_y), ok_button_size);

	okButton->SetBitmapHover(*ok_skin_hover);
	okButton->SetBitmapSelected(*ok_skin_click);
	//ok_button.Bind(wxEVT_BUTTON, self.initiate_connection);

	cancelButton = new wxBitmapButton(this, BUTTON_CANCEL, *cancel_skin,
		wxPoint(ok_button_x - 300, ok_button_y), cancel_button_size);

	cancelButton->SetBitmapHover(*cancel_skin_hover);
	cancelButton->SetBitmapSelected(*cancel_skin_hover);
	//Bind(wxEVT_BUTTON, &NewFrame::OnExit, this, BUTTON_CANCEL);
	//cancelButton->Connect( ((int)BUTTON_CANCEL,wxEVT_BUTTON, OnExit);


	//this->SetFocus();
}
MainFrame* NewFrame::getMain()
{
	return wxDynamicCast(parent, MainFrame);
}
void NewFrame::changeVolume(wxCommandEvent& evt)
{
	MainFrame * window = getMain();
	if (window != nullptr)
	{
		window->SetVolume(slider->GetValue());
	}
}

void NewFrame::KillFocus(wxFocusEvent& evt)
{
	wxWindow* w = evt.GetWindow();
	int id = w->GetId();
	if(id == BUTTON_CANCEL)
	{
		FadeOut();
	}
	if (id == BUTTON_QUIT_OK)
	{
		MainFrame* window = getMain();
		window->Close(TRUE);
	}
	this->SetFocus();
}
