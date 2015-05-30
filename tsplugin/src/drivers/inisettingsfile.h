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

#include "../interfaces/drivers.h"
#include <QPointer>
class QSettings;

namespace Driver
{

class IniSettingsFile : public QObject, public Interfaces::SettingsDriver
{
	Q_OBJECT

public:
	IniSettingsFile( QObject *parent );
	virtual ~IniSettingsFile();

	QVariant get( const QString &section, const QString &name, const QVariant &defaultValue );
	void set( const QString &section, const QString &name, const QVariant &value );

private:
	QPointer<QSettings> mySettings;
};

}
