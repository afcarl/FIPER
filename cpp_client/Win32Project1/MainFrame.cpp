#include "MainFrame.h"

wxBEGIN_EVENT_TABLE(MainFrame, wxFrame)
EVT_PAINT(MainFrame::OnPaint)
EVT_BUTTON(BUTTON_QUIT, MainFrame::OnExit)
EVT_BUTTON(BUTTON_CONNECT, MainFrame::OnConnect)
EVT_BUTTON(BUTTON_OPTIONS, MainFrame::OnOptions)
EVT_ERASE_BACKGROUND(MainFrame::OnErase)
EVT_MEDIA_LOADED(CONTROL_MEDIA, MainFrame::SongLoaded)
EVT_MEDIA_FINISHED(CONTROL_MEDIA, MainFrame::SongLoaded)
wxEND_EVENT_TABLE()


MainFrame::MainFrame(const wxString& title, const wxPoint& pos, const wxSize& size)
	: wxFrame(nullptr, WINDOW_MAIN, title, pos, size), newFrame(nullptr), mediaPlayer(nullptr)
{
	wxDisplaySize(&width, &height);
	
	this->HeightDefault(height);
	this->WidthDefault(width);
	button_hide = false;
	SetBackgroundColour("Black");
	// Image sources
	SetBackgroundStyle(wxBackgroundStyle::wxBG_STYLE_CUSTOM);
	wxInitAllImageHandlers(); //todo: myabe we dont need all
	SetButtonTextures();
}

void MainFrame::OnExit(wxCommandEvent& event)
{
	HideButtons();
	int x_pos = (this->width * 0.1);
	int	y_pos = (this->height * 0.3);
	int	width = (this->width * 0.5);
	int	height = (this->height * 0.5);
	newFrame = new NewFrame(WINDOW_QUIT, " Q U I T ", wxPoint(x_pos, y_pos), wxSize(width, height), this);

	//Close(TRUE); // Tells the OS to quit running this process
}

void MainFrame::OnConnect(wxCommandEvent& event)
{
	HideButtons();
		int x_pos = (this->width * 0.025);
		int	y_pos = (this->height * 0.025);
		int	width = (this->width * 0.95);
		int	height = (this->height * 0.95);
		//this->Connect(WINDOW_CONNECT, wxEVT_CLOSE_WINDOW, wxCloseEventHandler(MainFrame::OnNewFrameClose));
		newFrame = new NewFrame(WINDOW_CONNECT, " C O N N E C T ", wxPoint(x_pos, y_pos), wxSize(width, height), this);
		
}
void MainFrame::OnOptions(wxCommandEvent& event)
{
	HideButtons();
	int x_pos = (this->width * 0.1);
	int	y_pos = (this->height * 0.3);
	int	width = (this->width * 0.55);
	int	height = (this->height * 0.55);
	newFrame = new NewFrame(WINDOW_OPTIONS, " O P T I O N S ", wxPoint(x_pos, y_pos), wxSize(width, height), this);

	//Bind(wxEVT_KILL_FOCUS, &MainFrame::KillFocus);

	/*wxListBox connect_list(connectWindow, WINDOW_OPTIONS, wxPoint(width*0.05, height*0.4),
		wxSize(width*0.5, height*0.5), 0, NULL, wxTE_MULTILINE);
	connect_list.SetBackgroundColour("White");*/

}

void MainFrame::OnPaint(wxPaintEvent & evt)
{
	if (mediaPlayer == nullptr)
	{
	//	Music();
	}
	wxImage background_image("image/menu/bgnd.jpg", wxBITMAP_TYPE_JPEG);
	wxImage fiper_logo("image/menu/fiper_logo.png", wxBITMAP_TYPE_PNG);
	wxBitmap backgroundBm(background_image.Scale(width, height, wxImageResizeQuality::wxIMAGE_QUALITY_HIGH));
	wxBitmap logoBm(fiper_logo.Scale(width*0.4, height*0.3, wxImageResizeQuality::wxIMAGE_QUALITY_HIGH));
	wxPaintDC dc(this);

	dc.DrawBitmap(backgroundBm, 0, 0, true);
	dc.DrawBitmap(logoBm, 40, -10, false);
	wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
	dc.SetFont(font);
	dc.SetTextForeground("white");
	dc.DrawText("Version: Pre-Alpha", this->width*0.005, this->height*0.97);
	dc.DrawText("Contact: GAL.MATEO @ GMAIL.COM", width*0.77, height*0.97);
	// Custom cursor for the application
	SetCursor(wxCursor("image/menu/cursor.ico", wxBitmapType::wxBITMAP_TYPE_ICO));
	if (button_hide == false)
	{
		PlaceButtons();
	}
	
}
void MainFrame::SetButtonTextures()
{
	connect_skin = new wxBitmap("image/menu/buttons/btn0.png", wxBITMAP_TYPE_PNG);
	connect_skin_hover = new wxBitmap("image/menu/buttons/btn0_hover.png", wxBITMAP_TYPE_PNG);
	connect_skin_click = new wxBitmap("image/menu/buttons/btn0_click.png", wxBITMAP_TYPE_PNG);

	options_skin = new wxBitmap("image/menu/buttons/btn1.png", wxBITMAP_TYPE_PNG);
    options_skin_hover = new wxBitmap("image/menu/buttons/btn1_hover.png", wxBITMAP_TYPE_PNG);
	options_skin_click = new wxBitmap("image/menu/buttons/btn1_click.png", wxBITMAP_TYPE_PNG);

	quit_skin = new wxBitmap("image/menu/buttons/btn2.png", wxBITMAP_TYPE_PNG);
	quit_skin_hover = new wxBitmap("image/menu/buttons/btn2_hover.png", wxBITMAP_TYPE_PNG);
	quit_skin_click = new wxBitmap("image/menu/buttons/btn2_click.png", wxBITMAP_TYPE_PNG);

	ok_skin = new wxBitmap("image/menu/buttons/btn3.png", wxBITMAP_TYPE_PNG);
	ok_skin_hover = new wxBitmap("image/menu/buttons/btn3_hover.png", wxBITMAP_TYPE_PNG);
	ok_skin_click = new wxBitmap("image/menu/buttons/btn3_click.png", wxBITMAP_TYPE_PNG);

	cancel_skin = new wxBitmap("image/menu/buttons/btn4.png", wxBITMAP_TYPE_PNG);
	cancel_skin_hover = new wxBitmap("image/menu/buttons/btn4_hover.png", wxBITMAP_TYPE_PNG);
	cancel_skin_click = new wxBitmap("image/menu/buttons/btn4_click.png", wxBITMAP_TYPE_PNG);
}

void MainFrame::PlaceButtons()
{

	//FprButton*  con_button = new FprButton(this, BUTTON_CONNECT, "CONNECT", wxPoint((width*0.64), (height*0.3)), wxSize(510, 130));
	// Place buttons on the background and define the behaviour of them

	connect_button = new wxBitmapButton(this, BUTTON_CONNECT, *connect_skin, 
		wxPoint((width*0.64), (height*0.3)), 
		wxSize(510, 130));
	connect_button->SetBitmapHover(*connect_skin_hover);
	connect_button->SetBitmapSelected(*connect_skin_click);
	//connect_button->Bind(wx.EVT_BUTTON, connect_window);
	
	options_button = new wxBitmapButton(this, BUTTON_OPTIONS, *options_skin,
		wxPoint((width*0.64), (height*0.5)),
		wxSize(510, 130));
	options_button->SetBitmapHover(*options_skin_hover);
	options_button->SetBitmapSelected(*options_skin_click);
	//options_button->Bind(wx.EVT_BUTTON, options_window);

	quit_button = new wxBitmapButton(this, BUTTON_QUIT, *quit_skin,
		wxPoint((width*0.64), (height*0.7)),
		wxSize(510, 130));
	quit_button->SetBitmapHover(*quit_skin_hover);
	quit_button->SetBitmapSelected(*quit_skin_click);
	//quit_button.Bind(wx.EVT_BUTTON, quit_window);
}


void MainFrame::show_buttons()
{

	/*this->connect_button->Show();
	options_button->Show();
	quit_button->Show();*/
	button_hide = false;
    PlaceButtons();

}

void MainFrame::HideButtons()
{
	/*connect_button->Hide();
	options_button->Hide();
	quit_button->Hide();*/

	connect_button->Destroy();
	options_button->Destroy();
	quit_button->Destroy();
	button_hide = true;
	wxClientDC dc(this);
	
	wxImage background_image("image/menu/bgnd.jpg", wxBITMAP_TYPE_JPEG);
	wxImage fiper_logo("image/menu/fiper_logo.png", wxBITMAP_TYPE_PNG);
	wxBitmap backgroundBm(background_image.Scale(width, height, wxImageResizeQuality::wxIMAGE_QUALITY_HIGH));
	wxBitmap logoBm(fiper_logo.Scale(width*0.4, height*0.3, wxImageResizeQuality::wxIMAGE_QUALITY_HIGH));
	dc.Clear();
	dc.DrawBitmap(backgroundBm, 0, 0, true);
	dc.DrawBitmap(logoBm, 40, -10, false);
	wxFont font(14, wxFONTFAMILY_TELETYPE, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false);
	dc.SetFont(font);
	dc.SetTextForeground("white");
	dc.DrawText("Version: Pre-Alpha", this->width*0.005, this->height*0.97);
	dc.DrawText("Contact: GAL.MATEO @ GMAIL.COM", width*0.77, height*0.97);
	
}

MainFrame::~MainFrame()
{
	/*delete connect_button;
	delete options_button;
	delete quit_button;

	delete connect_skin;
	delete connect_skin_hover;
	delete connect_skin_click;
	delete options_skin;
	delete options_skin_hover;
	delete options_skin_click;
	delete quit_skin;
	delete quit_skin_hover;
	delete quit_skin_click;
	delete ok_skin;
	delete ok_skin_hover;
	delete ok_skin_click;
	delete cancel_skin;
	delete cancel_skin_hover;
	delete cancel_skin_click;*/
}

//must override to dont do anything at erase!
void MainFrame::OnErase(wxEraseEvent& event)
{
}

void MainFrame::Music()
{
	//we need different players in different OS
	#if defined(WIN32)
	wxString backend(wxMEDIABACKEND_WMP10);
	#else
	wxString backend(wxEmptyString);
	#endif

	mediaPlayer = new wxMediaCtrl(this, CONTROL_MEDIA,
		wxString("audio/music/carpenter_brut.mp3"),
		wxDefaultPosition,
		wxSize(0, 0),
		0,
		backend);
}
void MainFrame::SetVolume(int vol)
{
	if(mediaPlayer)
		mediaPlayer->SetVolume(((double)vol)/10);
}


void MainFrame::SongLoaded(wxMediaEvent& evt)
{
	mediaPlayer->Play();
}

