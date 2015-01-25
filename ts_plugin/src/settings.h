#pragma once

#include "modulebase.h"
#include "ui/settingsdialog.h"
#include <QPointer>

class QSettings;

class Settings : public ModuleBase, public SettingsInterface
{
	Q_OBJECT

public:
	Settings( QObject *parent = 0 );

	virtual int providesAudioBackend() const { return -1; }
	virtual void configure( void* handle, void* qParentWidget );
	virtual void onMenuItemEvent( uint64 serverConnectionHandlerID, PluginMenuType type, int menuItemID, uint64 selectedItemID );

	virtual bool isPositionalAudioEnabled() const;
	virtual void setPositionalAudioEnabled( bool enabled );
	virtual int getAudioBackend() const;
	virtual void setAudioBackend( int backend );

signals:
	void positionalAudioToggled( bool enabled );
	void audioBackendChanged( int backend );

private:
	QWidget* getMainWindowWidget() const;
	void openSettingsDialog( QWidget *parent );

private:
	QPointer<QSettings> mySettings;
	QPointer<SettingsDialog> dialog;
};

