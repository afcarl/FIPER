// wxWidgets "Hello world" Program
// For compilers that support precompilation, includes "wx/wx.h".

#include "MainFrame.h"

class MyApp : public wxApp
{
public:
	virtual bool OnInit();
};


wxBEGIN_EVENT_TABLE(MainFrame, wxFrame)
EVT_PAINT(MainFrame::OnPaint)
EVT_BUTTON(BUTTON_QUIT, MainFrame::OnExit) // Tell the OS to run MainFrame::OnExit when
EVT_BUTTON(BUTTON_CONNECT, MainFrame::OnConnect) // Tell the OS to run MainFrame::OnExit when
EVT_BUTTON(BUTTON_OPTIONS, MainFrame::OnOptions) // Tell the OS to run MainFrame::OnExit when
EVT_LEFT_UP(MainFrame::Click)
EVT_KILL_FOCUS(MainFrame::KillFocus)
EVT_SET_FOCUS(MainFrame::SetFocus)
EVT_ERASE_BACKGROUND(MainFrame::OnErase)
EVT_MEDIA_LOADED(CONTROL_MEDIA, MainFrame::SongLoaded)
EVT_MEDIA_FINISHED(CONTROL_MEDIA, MainFrame::SongLoaded)
wxEND_EVENT_TABLE()

wxBEGIN_EVENT_TABLE(NewFrame, wxFrame)
EVT_PAINT(NewFrame::OnPaint)
EVT_KEY_DOWN(NewFrame::key_stroke_callback)
EVT_SLIDER(SLIDER_VOLUME, NewFrame::changeVolume)
//EVT_FOCUS(NewFrame::KillFocus)
wxEND_EVENT_TABLE()

wxBEGIN_EVENT_TABLE(FprButton, wxFrame)
EVT_PAINT(FprButton::OnPaint)
wxEND_EVENT_TABLE()


wxIMPLEMENT_APP(MyApp);
bool MyApp::OnInit()
{
	MainFrame *frame = new MainFrame("FIPER", wxPoint(50, 50), wxSize(450, 340));
	//frame->Show(true);
	frame->ShowFullScreen(true);
	return true;
}
