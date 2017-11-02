// wxWidgets "Hello world" Program
// For compilers that support precompilation, includes "wx/wx.h".

#include "MainFrame.h"

class MyApp : public wxApp
{
public:
	virtual bool OnInit();
};

wxIMPLEMENT_APP(MyApp);
bool MyApp::OnInit()
{
	MainFrame *frame = new MainFrame("FIPER", wxPoint(50, 50), wxSize(450, 340));
	//frame->Show(true);
	frame->ShowFullScreen(true);
	return true;
}
