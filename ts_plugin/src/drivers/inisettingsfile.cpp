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

#include "inisettingsfile.h"
#include <QSettings>
#include <iostream>

namespace Driver
{

IniSettingsFile::IniSettingsFile( QObject *parent )
	: QObject( parent )
{
	mySettings = new QSettings(
		QSettings::IniFormat,
		QSettings::UserScope,
		"jhakonen.com",
		"WOTTessuMod"
	);
	std::cout << "TessuMod settings are stored to: " << mySettings->fileName().toStdString() << std::endl;
}

IniSettingsFile::~IniSettingsFile()
{
	delete mySettings;
}

QVariant IniSettingsFile::get( const QString &section, const QString &name, const QVariant &defaultValue )
{
	bool useGroup = section.toLower() != "general";
	if( useGroup )
	{
		mySettings->beginGroup( section );
	}
	QVariant result = mySettings->value( name, defaultValue );
	if( useGroup )
	{
		mySettings->endGroup();
	}
	return result;
}

void IniSettingsFile::set( const QString &section, const QString &name, const QVariant &value )
{
	bool useGroup = section.toLower() != "general";
	if( useGroup )
	{
		mySettings->beginGroup( section );
	}
	mySettings->setValue( name, value );
	if( useGroup )
	{
		mySettings->endGroup();
	}
}

}
