#pragma once
#include <wx/wxprec.h>
#include <wx/wx.h>
#include <wx/msgdlg.h>
#include <wx/mediactrl.h>
#include "NewFrame.h"
#include "FprButton.h"
#include "ids.h"

class NewFrame;

class MainFrame : public wxFrame
{
public:
	MainFrame(const wxString& title, const wxPoint& pos, const wxSize& size);
	void OnErase(wxEraseEvent& event);
	~MainFrame();
	void show_buttons();
	void SongLoaded(wxMediaEvent& evt);
	void SetVolume(int vol);
private:
	void SetButtonTextures();
	void PlaceButtons();
	
	void HideButtons();
	void OnPaint(wxPaintEvent & evt);
	void OnExit(wxCommandEvent& event);
	void OnConnect(wxCommandEvent& event);
	void OnOptions(wxCommandEvent& event);
	void Music();
	int width;
	int height;

	//Layout
	wxFrame* Buttons;
	//windows
	NewFrame* newFrame;

	wxMediaCtrl* mediaPlayer;

	//buttons
	wxBitmapButton* connect_button;
	wxBitmapButton* options_button;
	wxBitmapButton* quit_button;

	bool button_hide;
	//button textures
	wxBitmap* connect_skin;
	wxBitmap* connect_skin_hover;
	wxBitmap* connect_skin_click;
	wxBitmap* options_skin;
	wxBitmap* options_skin_hover;
	wxBitmap* options_skin_click;
	wxBitmap* quit_skin;
	wxBitmap* quit_skin_hover;
	wxBitmap* quit_skin_click;
	wxBitmap* ok_skin;
	wxBitmap* ok_skin_hover;
	wxBitmap* ok_skin_click;
	wxBitmap* cancel_skin;
	wxBitmap* cancel_skin_hover;
	wxBitmap* cancel_skin_click;
	wxDECLARE_EVENT_TABLE();
};

