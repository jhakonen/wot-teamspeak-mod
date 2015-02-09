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

#include "logging.h"
#include "../entities/vector.h"

#include <QTextStream>

namespace {

Log::Sink *gLogSink = NULL;

}

namespace Log
{

Stream debug()
{
	Stream stream;
	stream.severity = Debug;
	return stream;
}

Stream info()
{
	Stream stream;
	stream.severity = Info;
	return stream;
}

Stream warning()
{
	Stream stream;
	stream.severity = Warning;
	return stream;
}

Stream error()
{
	Stream stream;
	stream.severity = Error;
	return stream;
}

void setSink( Sink *sink )
{
	gLogSink = sink;
}

Stream::~Stream()
{
	if( gLogSink )
	{
		gLogSink->logMessage( message, severity );
	}
}

Stream &operator<<( Stream &stream, const QString &value )
{
	QTextStream textStream( &stream.message );
	textStream << value;
	return stream;
}

Stream &operator<<( Stream &stream, quint16 value )
{
	QTextStream textStream( &stream.message );
	textStream << value;
	return stream;
}

Stream &operator<<( Stream &stream, const Entity::Vector &value )
{
	QTextStream textStream( &stream.message );
	textStream << "(" << value.x << ", " << value.y << ", " << value.z << ")";
	return stream;
}

}
