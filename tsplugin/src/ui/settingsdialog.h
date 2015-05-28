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

class QStandardItemModel;
class QAbstractButton;

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

	bool isHrtfEnabled() const;
	void setHrtfEnabled( bool enabled );

	QString getHrtfDataSet() const;
	void setHrtfDataSet( const QString &name );

	int getLoggingLevel() const;
	void setLoggingLevel( int level );

	void showTestAudioError( const QString &error );
	void setTestButtonEnabled( bool enabled );

	void setHrtfDataFileNames( const QStringList &fileNames );

	void setOpenALConfFilePath( const QString &filePath );

private slots:
	void on_testButton_clicked();
	void on_openALRadioButton_toggled(bool checked);
	void on_builtinAudioRadioButton_toggled();
	void on_enableHrtfCheckBox_toggled();
	void on_positionalAudioCheckBox_toggled();
	void on_buttonBox_clicked( QAbstractButton *button );
	void on_loggingLevelComboBox_currentIndexChanged( int index );
	void on_openALAdvancedButton_clicked();
	void onHrtfSelectionChanged();

signals:
	void applied();
	void testButtonClicked();

private:
	bool areSettingsUnapplied() const;
	void enableApplyButton( bool enabled );

private:
	Ui::SettingsDialog *ui;
	QStandardItemModel *hrtfDataSetsModel;
	int audioBackend;
	bool positionalAudioEnabled;
	bool hrtfEnabled;
	int loggingLevel;
	QString hrtfDataSet;
	QString openALConfFilePath;
};
