#pragma once

#include <QDialog>

namespace Ui {
class SettingsDialog;
}

class SettingsInterface
{
public:
	virtual bool isPositionalAudioEnabled() const = 0;
	virtual void setPositionalAudioEnabled( bool enabled ) = 0;
	virtual int getAudioBackend() const = 0;
	virtual void setAudioBackend( int backend ) = 0;
};

class SettingsDialog : public QDialog
{
	Q_OBJECT

public:
	SettingsDialog( SettingsInterface *settings, QWidget *parent = 0 );
	~SettingsDialog();

private slots:
	void onApply();

private:
	SettingsInterface *settings;
	Ui::SettingsDialog *ui;
};
