#include "settings.h"
#include "ts_helpers.h"
#include "ui/settingsdialog.h"
#include <plugin_definitions.h>
#include <iostream>
#include <QApplication>
#include <QWindow>
#include <QSettings>

Settings::Settings( QObject *parent )
	: ModuleBase( parent )
{
	mySettings = new QSettings(
		QSettings::IniFormat,
		QSettings::UserScope,
		"jhakonen.com",
		"WOTTessuMod",
		this
	);
	std::cout << "TessuMod settings are stored to: " << mySettings->fileName().toStdString() << std::endl;
}

void Settings::configure( void *handle, void *qParentWidget )
{
	Q_UNUSED( handle );
	openSettingsDialog( (QWidget*)qParentWidget );
}

void Settings::onMenuItemEvent( uint64 serverConnectionHandlerID, PluginMenuType type, int menuItemID, uint64 selectedItemID )
{
	Q_UNUSED( serverConnectionHandlerID );
	Q_UNUSED( selectedItemID );

	switch( type )
	{
	case PLUGIN_MENU_TYPE_GLOBAL:
		switch( menuItemID )
		{
		case MENU_ID_GLOBAL_SETTINGS:
			openSettingsDialog( getMainWindowWidget() );
			break;
		default:
			break;
		}
		break;
	default:
		break;
	}
}

bool Settings::isPositionalAudioEnabled() const
{
	return mySettings->value( "PositionalAudioEnabled", true ).toBool();
}

void Settings::setPositionalAudioEnabled( bool enabled )
{
	if( isPositionalAudioEnabled() != enabled )
	{
		mySettings->setValue( "PositionalAudioEnabled", enabled );
		emit positionalAudioToggled( enabled );
	}
}

int Settings::getAudioBackend() const
{
	return mySettings->value( "AudioBackend", OpenALBackend ).toInt();
}

void Settings::setAudioBackend( int backend )
{
	if( getAudioBackend() != backend )
	{
		mySettings->setValue( "AudioBackend", backend );
		emit audioBackendChanged( backend );
	}
}

QWidget* Settings::getMainWindowWidget() const
{
	foreach( QWidget *widget, QApplication::topLevelWidgets() )
	{
		if( widget->isWindow() && widget->inherits( "QMainWindow" ) && !widget->windowTitle().isEmpty() )
		{
			return widget;
		}
	}
	return NULL;
}

void Settings::openSettingsDialog( QWidget* parent )
{
	dialog = new SettingsDialog( this, parent );
	dialog->exec();
	delete dialog;
}
