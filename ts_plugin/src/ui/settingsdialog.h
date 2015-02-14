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

#pragma once

#include <QDialog>
#include "../entities/enums.h"

namespace Ui {
class SettingsDialog;
}

class SettingsDialog : public QDialog
{
	Q_OBJECT

public:
	SettingsDialog( QWidget *parent = 0 );
	~SettingsDialog();

	bool getPositionalAudioEnabled() const;
	void setPositionalAudioEnabled( bool enabled );

	int getAudioBackend() const;
	void setAudioBackend( int backend );

	Entity::RotateMode getRotateMode() const;
	void setRotateMode( Entity::RotateMode mode );

	Entity::Channels getChannels() const;
	void setChannels( Entity::Channels channels );

	bool isHrtfEnabled() const;
	void setHrtfEnabled( bool enabled );

	QString getHrtfDataSet() const;
	void setHrtfDataSet( const QString &name );

	bool isLoggingEnabled() const;
	void setLoggingEnabled( bool enabled );

private slots:
	void on_testButton_clicked();
	void on_showLogsButton_clicked();

signals:
	void applied();
	void testButtonClicked();

private:
	Ui::SettingsDialog *ui;
};
