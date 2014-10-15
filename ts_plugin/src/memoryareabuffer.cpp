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

#include "memoryareabuffer.h"
#include <cstring>

MemoryAreaBuffer::MemoryAreaBuffer( QObject* parent )
	: QIODevice( parent ), memoryData( 0 ), memorySize( 0 )
{
}

void MemoryAreaBuffer::setMemoryArea( void* data, int size )
{
	memoryData = data;
	memorySize = size;
}

bool MemoryAreaBuffer::open( QIODevice::OpenMode mode )
{
	return QIODevice::open( mode | Unbuffered );
}

qint64 MemoryAreaBuffer::readData( char* data, qint64 maxSize )
{
	if ( isOpen() )
	{
		qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
		memcpy( data, (char*)memoryData + pos(), size );
		return size;
	}
	return -1;
}

qint64 MemoryAreaBuffer::writeData( const char* data, qint64 maxSize )
{
	if ( isOpen() )
	{
		qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
		memcpy( (char*)memoryData + pos(), data, size );
		return size;
	}
	return -1;

}
