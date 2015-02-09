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
		connect( settingsDialog, SIGNAL(applied()), this, SLOT(onSettingsChanged()) );
		connect( settingsDialog, SIGNAL(finished(int)), settingsDialog, SLOT(deleteLater()) );
		settingsDialog->setModal( true );
		settingsDialog->show();
	}
}

void UiAdapter::onSettingsChanged()
{
	if( settingsDialog )
	{
		originalSettings.positioningEnabled = settingsDialog->getPositionalAudioEnabled();
		originalSettings.audioBackend = (Entity::AudioBackend) settingsDialog->getAudioBackend();
		useCaseFactory->saveSettings( originalSettings );
	}
}

}
