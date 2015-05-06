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
#include "../utils/logging.h"

#include <QPushButton>
#include <QTooltip>
#include <QStandardItemModel>
#include <QSortFilterProxyModel>
#include <QFileInfo>

#include <iostream>

SettingsDialog::SettingsDialog( QWidget *parent )
	: QDialog( parent ), ui( new Ui::SettingsDialog )
{
	ui->setupUi( this );
	hrtfDataSetsModel = new QStandardItemModel( this );
	QSortFilterProxyModel *sortProxy = new QSortFilterProxyModel( this );
	sortProxy->setSourceModel( hrtfDataSetsModel );
	sortProxy->setSortRole( Qt::UserRole + 1 );
	sortProxy->sort( 0, Qt::AscendingOrder );
	ui->hrtfDataSetListView->setModel( sortProxy );
	connect( ui->hrtfDataSetListView->selectionModel(), SIGNAL(currentChanged(QModelIndex, QModelIndex)),
			 this, SLOT(onHrtfSelectionChanged()) );
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
	positionalAudioEnabled = enabled;
	enableApplyButton( areSettingsUnapplied() );
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
	audioBackend = backend;
	enableApplyButton( areSettingsUnapplied() );
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
	hrtfEnabled = enabled;
	enableApplyButton( areSettingsUnapplied() );
}

QString SettingsDialog::getHrtfDataSet() const
{
	QModelIndex index = ui->hrtfDataSetListView->selectionModel()->currentIndex();
	if( index.isValid() )
	{
		return index.data( Qt::UserRole ).toString();
	}
	return "";
}

void SettingsDialog::setHrtfDataSet( const QString &name )
{
	QAbstractItemModel *m = ui->hrtfDataSetListView->model();
	QModelIndexList matches = m->match( m->index( 0, 0 ), Qt::UserRole, name, 1 );
	if( matches.isEmpty() )
	{
		Log::warning() << "HRTF dataset not found from dataset list";
		return;
	}
	ui->hrtfDataSetListView->selectionModel()->setCurrentIndex(
				matches[0], QItemSelectionModel::SelectCurrent );
	hrtfDataSet = name;
	enableApplyButton( areSettingsUnapplied() );
}

bool SettingsDialog::isLoggingEnabled() const
{
	return ui->enableLoggingCheckBox->isChecked();
}

void SettingsDialog::setLoggingEnabled( bool enabled )
{
	ui->enableLoggingCheckBox->setChecked( enabled );
	loggingEnabled = enabled;
	enableApplyButton( areSettingsUnapplied() );
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

void SettingsDialog::setHrtfDataPaths( const QStringList &paths )
{
	Log::debug() << "SettingsDialog::setHrtfDataPaths()";
	hrtfDataSetsModel->clear();
	foreach( QString path, paths )
	{
		QString name = QFileInfo( path )
				.baseName()
				.replace( "-", " " )
				.replace( "_", " " )
				.trimmed()
				.toUpper();

		QString sortValue = name;
		if( name.contains( "MIT KEMAR" ) )
		{
			sortValue = "1" + sortValue;
		}
		else if( name.contains( "CIAIR" ) )
		{
			sortValue = "2" + sortValue;
		}
		else
		{
			sortValue = "3" + sortValue;
		}

		QStandardItem *item = new QStandardItem( name );
		item->setData( path, Qt::UserRole );
		item->setData( sortValue, Qt::UserRole + 1 );
		hrtfDataSetsModel->appendRow( item );
	}
	enableApplyButton( areSettingsUnapplied() );
}

void SettingsDialog::on_testButton_clicked()
{
	emit testButtonClicked();
}

void SettingsDialog::on_openALRadioButton_toggled( bool checked )
{
	ui->openALGroupBox->setEnabled( checked );
	enableApplyButton( areSettingsUnapplied() );
}

void SettingsDialog::on_builtinAudioRadioButton_toggled()
{
	enableApplyButton( areSettingsUnapplied() );
}

void SettingsDialog::on_enableHrtfCheckBox_toggled()
{
	enableApplyButton( areSettingsUnapplied() );
}

void SettingsDialog::on_positionalAudioCheckBox_toggled()
{
	enableApplyButton( areSettingsUnapplied() );
}

void SettingsDialog::onHrtfSelectionChanged()
{
	enableApplyButton( areSettingsUnapplied() );
}

bool SettingsDialog::areSettingsUnapplied() const
{
	return !(
		getPositionalAudioEnabled() == positionalAudioEnabled &&
		getAudioBackend() == audioBackend &&
		isHrtfEnabled() == hrtfEnabled &&
		getHrtfDataSet() == hrtfDataSet &&
		isLoggingEnabled() == loggingEnabled
	);
}

void SettingsDialog::enableApplyButton( bool enabled )
{
	ui->buttonBox->button( QDialogButtonBox::Apply )->setEnabled( enabled );
}

void SettingsDialog::on_buttonBox_clicked( QAbstractButton *button )
{
	if( button == ui->buttonBox->button( QDialogButtonBox::Apply ) ||
		button == ui->buttonBox->button( QDialogButtonBox::Ok ) )
	{
		emit applied();
		positionalAudioEnabled = getPositionalAudioEnabled();
		audioBackend = getAudioBackend();
		hrtfEnabled = isHrtfEnabled();
		hrtfDataSet = getHrtfDataSet();
		loggingEnabled = isLoggingEnabled();
		enableApplyButton( areSettingsUnapplied() );
	}
}
