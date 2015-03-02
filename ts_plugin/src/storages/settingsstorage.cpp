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

#include "settingsstorage.h"
#include "../entities/settings.h"
#include "../interfaces/drivers.h"

namespace Storage
{

SettingsStorage::SettingsStorage( Interfaces::SettingsDriver *driver, QObject *parent )
	: QObject( parent ), driver( driver )
{
}

Entity::Settings SettingsStorage::get() const
{
	Entity::Settings settings;
	settings.audioBackend        = (Entity::AudioBackend) driver->get( "General", "AudioBackend", (int)Entity::OpenALBackend ).toInt();
	settings.positioningEnabled  = driver->get( "General", "PositionalAudioEnabled", true ).toBool();
	settings.testRotateMode      = (Entity::RotateMode) driver->get( "General", "TestRotateMode", Entity::RotateYAxis ).toInt();
	settings.hrtfEnabled         = driver->get( "General", "HrtfEnabled", false ).toBool();
	settings.hrtfDataSet         = driver->get( "General", "HrtfDataSet", ":/etc/hrtfs/mit_kemar-44100.mhr" ).toString();
	settings.audioLoggingEnabled = driver->get( "General", "AudioLoggingEnabled", false ).toBool();
	return settings;
}

void SettingsStorage::set( const Entity::Settings &settings )
{
	driver->set( "General", "AudioBackend",           (int)settings.audioBackend );
	driver->set( "General", "PositionalAudioEnabled", settings.positioningEnabled );
	driver->set( "General", "TestRotateMode",         (int)settings.testRotateMode );
	driver->set( "General", "HrtfEnabled",            settings.hrtfEnabled );
	driver->set( "General", "HrtfDataSet",            settings.hrtfDataSet );
	driver->set( "General", "AudioLoggingEnabled",    settings.audioLoggingEnabled );
}

}
