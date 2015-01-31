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

#include "uiadapter.h"
#include "../interfaces/usecasefactory.h"
#include "../entities/settings.h"
#include "../ui/settingsdialog.h"
#include "../utils/logging.h"
#include <iostream>

namespace Adapter
{

UiAdapter::UiAdapter( Interfaces::UseCaseFactory *useCaseFactory, QObject *parent )
	: QObject( parent ), useCaseFactory( useCaseFactory )
{
}

void UiAdapter::showSettingsUi( const Entity::Settings &settings, QWidget *parent )
{
	Log::info() << "UiAdapter::showSettingsUi()";
	if( !settingsDialog )
	{
		originalSettings = settings;
		settingsDialog = new SettingsDialog( parent );

		settingsDialog->setPositionalAudioEnabled( settings.positioningEnabled );
		settingsDialog->setAudioBackend( settings.audioBackend );
		settingsDialog->setRotateMode( settings.testRotateMode );
		settingsDialog->setChannels( settings.audioChannels );
		settingsDialog->setHrtfEnabled( settings.hrtfEnabled );
		settingsDialog->setHrtfDataSet( settings.hrtfDataSet );
		settingsDialog->setLoggingEnabled( settings.audioLoggingEnabled );

		connect( settingsDialog, SIGNAL(applied()), this, SLOT(onSettingsChanged()) );
		connect( settingsDialog, SIGNAL(testButtonClicked()), this, SLOT(onTestButtonClicked()) );
		connect( settingsDialog, SIGNAL(finished(int)), settingsDialog, SLOT(deleteLater()) );

		settingsDialog->setModal( true );
		settingsDialog->show();
	}
}

void UiAdapter::onSettingsChanged()
{
	useCaseFactory->saveSettings( collectSettingsFromUI() );
}

void UiAdapter::onTestButtonClicked()
{
	useCaseFactory->playTestAudioWithSettings( collectSettingsFromUI() );
}

Entity::Settings UiAdapter::collectSettingsFromUI() const
{
	Entity::Settings settings = originalSettings;
	if( settingsDialog )
	{
		settings.positioningEnabled = settingsDialog->getPositionalAudioEnabled();
		settings.audioBackend = (Entity::AudioBackend) settingsDialog->getAudioBackend();
		settings.testRotateMode = settingsDialog->getRotateMode();
		settings.audioChannels = settingsDialog->getChannels();
		settings.hrtfEnabled = settingsDialog->isHrtfEnabled();
		settings.hrtfDataSet = settingsDialog->getHrtfDataSet();
		settings.audioLoggingEnabled = settingsDialog->isLoggingEnabled();
	}
	return settings;
}

}
