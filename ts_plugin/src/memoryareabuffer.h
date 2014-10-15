/*
 * TessuMod: Mod for integrating TeamSpeak into World of Tanks
 * Copyright (C) 2014  Janne Hakonen
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
#include <QIODevice>

class MemoryAreaBuffer : public QIODevice
{
	Q_OBJECT

public:
	MemoryAreaBuffer( QObject *parent = 0 );

	void setMemoryArea( void* data, int size );

	virtual bool open( OpenMode mode );

protected:
	virtual qint64 readData( char* data, qint64 maxSize );
	virtual qint64 writeData( const char* data, qint64 maxSize );

private:
	void* memoryData;
	qint64 memorySize;
};
