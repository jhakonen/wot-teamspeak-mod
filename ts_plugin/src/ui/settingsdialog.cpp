#include "settingsdialog.h"
#include "ui_settingsdialog.h"
#include "../ts_helpers.h"
#include <QPushButton>
#include <iostream>

SettingsDialog::SettingsDialog( SettingsInterface *settings, QWidget *parent )
	: QDialog( parent ), ui( new Ui::SettingsDialog ), settings( settings )
{
	ui->setupUi( this );
	connect( ui->buttonBox->button( QDialogButtonBox::Apply ), SIGNAL(clicked()),
			 this, SLOT(onApply()) );
	connect( ui->buttonBox->button( QDialogButtonBox::Ok ), SIGNAL(clicked()),
			 this, SLOT(onApply()) );
	ui->builtinAudioRadioButton->setChecked( settings->getAudioBackend() == BuiltInBackend );
	ui->openALRadioButton->setChecked( settings->getAudioBackend() == OpenALBackend );
	ui->positionalAudioCheckBox->setEnabled( settings->isPositionalAudioEnabled() );
}

SettingsDialog::~SettingsDialog()
{
	delete ui;
}

void SettingsDialog::onApply()
{
	std::cout << "ACCEPT" << std::endl;
	settings->setPositionalAudioEnabled( ui->positionalAudioCheckBox->isChecked() );
	settings->setAudioBackend( ui->openALRadioButton->isChecked()? OpenALBackend:
							   ui->positionalAudioCheckBox->isChecked()? BuiltInBackend:
							   NoBackend );
}

