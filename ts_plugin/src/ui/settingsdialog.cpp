/*
 * TessuMod: Mod for integrating TeamSpeak into World of Tanks
 * Copyright (C) 2015  Janne Hakonen
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
 * USA
 */

#include "settingsdialog.h"
#include "ui_settingsdialog.h"
#include "../entities/enums.h"

#include <QPushButton>
#include <QTooltip>
#include <iostream>

SettingsDialog::SettingsDialog( QWidget *parent )
	: QDialog( parent ), ui( new Ui::SettingsDialog )
{
	ui->setupUi( this );
	connect( ui->buttonBox->button( QDialogButtonBox::Apply ), SIGNAL(clicked()),
			 this, SIGNAL(applied()) );
	connect( ui->buttonBox->button( QDialogButtonBox::Ok ), SIGNAL(clicked()),
			 this, SIGNAL(applied()) );
}

SettingsDialog::~SettingsDialog()
{
	delete ui;
}

bool SettingsDialog::getPositionalAudioEnabled() const
{
	return ui->positionalAudioCheckBox->isChecked();
}

void SettingsDialog::setPositionalAudioEnabled( bool enabled )
{
	ui->positionalAudioCheckBox->setChecked( enabled );
}

int SettingsDialog::getAudioBackend() const
{
	if( ui->openALRadioButton->isChecked() )
	{
		return Entity::OpenALBackend;
	}
	if( ui->builtinAudioRadioButton->isChecked() )
	{
		return Entity::BuiltInBackend;
	}
	return Entity::NoBackend;
}

void SettingsDialog::setAudioBackend( int backend )
{
	switch( backend )
	{
	case Entity::OpenALBackend:
		ui->openALRadioButton->setChecked( true );
		break;
	case Entity::BuiltInBackend:
		ui->builtinAudioRadioButton->setChecked( true );
		break;
	}
}

Entity::RotateMode SettingsDialog::getRotateMode() const
{
	return ui->rotateXRadioButton->isChecked()? Entity::RotateXAxis:
		ui->rotateYRadioButton->isChecked()? Entity::RotateYAxis:
		Entity::RotateZAxis;
}

void SettingsDialog::setRotateMode( Entity::RotateMode mode )
{
	ui->rotateXRadioButton->setChecked( mode == Entity::RotateXAxis );
	ui->rotateYRadioButton->setChecked( mode == Entity::RotateYAxis );
	ui->rotateZRadioButton->setChecked( mode == Entity::RotateZAxis );
}

bool SettingsDialog::isHrtfEnabled() const
{
	return ui->enableHrtfCheckBox->isChecked();
}

void SettingsDialog::setHrtfEnabled( bool enabled )
{
	ui->enableHrtfCheckBox->setChecked( enabled );
}

QString SettingsDialog::getHrtfDataSet() const
{
	// TODO
	return "";
}

void SettingsDialog::setHrtfDataSet( const QString &name )
{
	// TODO
}

bool SettingsDialog::isLoggingEnabled() const
{
	return ui->enableLoggingCheckBox->isChecked();
}

void SettingsDialog::setLoggingEnabled( bool enabled )
{
	ui->enableLoggingCheckBox->setChecked( enabled );
}

void SettingsDialog::showTestAudioError( const QString &error )
{
	QSize quarter = ui->testButton->size() / 2;
	QPoint center = QPoint( quarter.width(), quarter.height() );
	QToolTip::showText( ui->testButton->mapToGlobal( center ), error, ui->testButton );
}

void SettingsDialog::setTestButtonEnabled( bool enabled )
{
	ui->testButton->setEnabled( enabled );
}

void SettingsDialog::on_testButton_clicked()
{
	emit testButtonClicked();
}

void SettingsDialog::on_openALRadioButton_toggled( bool checked )
{
	ui->openALGroupBox->setEnabled( checked );
}
