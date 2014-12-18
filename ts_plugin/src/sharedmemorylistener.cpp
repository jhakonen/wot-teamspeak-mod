#include "sharedmemorylistener.h"
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
#include "ts_helpers.h"

#include <QTimer>
#include <QSharedMemory>
#include <QBuffer>
#include <QDataStream>
#include <QDebug>
#include <QDateTime>
#include <iostream>

static const int VERSION_SIZE = 2;
static const int TIME_LIMIT = 5;

class MyDataStream : public QDataStream
{
public:
	MyDataStream( QIODevice* device )
		: QDataStream( device )
	{
		setVersion( QDataStream::Qt_5_2 );
		setByteOrder( QDataStream::LittleEndian );
		setFloatingPointPrecision( QDataStream::SinglePrecision );
	}
};

SharedMemoryListener::SharedMemoryListener()
	: timer( new QTimer( this ) ), memory( new QSharedMemory( this ) )
{
	connect( timer, SIGNAL( timeout()), this, SLOT( onTimeout() ) );
	timer->setInterval( 100 );
	timer->setSingleShot( false );
	memory->setNativeKey( "TessuModTSPlugin3dAudio" );
}

SharedMemoryListener::~SharedMemoryListener()
{
	stop();
}

void SharedMemoryListener::start()
{
	timer->start();
	if ( connectToSharedMemory() == false )
	{
		QString message = "Failed to connect to shared memory, reason: "
				+ memory->errorString();
		std::cout << message.toStdString() << std::endl;
		stop();
		return;
	}
	memoryBuffer = new MemoryAreaBuffer( this );
	memoryBuffer->setMemoryArea( memory->data(), memory->size() );
	if ( memoryBuffer->open( QIODevice::ReadWrite ) == false )
	{
		std::cout << "Failed to open buffer" << std::endl;
		return;
	}
	MyDataStream stream( memoryBuffer );
	stream << (quint16) 1; // version*/
}

void SharedMemoryListener::stop()
{
	timer->stop();
}

void SharedMemoryListener::onTimeout()
{
	memoryBuffer->seek( 0 );
	MyDataStream stream( memoryBuffer );
	PositionalAudioData data;
	stream >> data;

	if( ( QDateTime::currentDateTime().toTime_t() - data.timestamp ) > TIME_LIMIT )
	{
		data.audioBackend = NoBackend;
		data.cameraPosition = createVector( 0, 0, 0 );
		data.cameraDirection = createVector( 0, 0, 0 );
		data.clientPositions.clear();
	}

	if( data.audioBackend != previousData.audioBackend )
	{
		emit audioBackendChanged( data.audioBackend );
	}
	if ( data.cameraPosition != previousData.cameraPosition )
	{
		emit cameraPositionChanged( data.cameraPosition );
	}
	if ( data.cameraDirection != previousData.cameraDirection )
	{
		emit cameraDirectionChanged( data.cameraDirection );
	}
	for ( auto iter = data.clientPositions.cbegin(); iter != data.clientPositions.cend(); ++iter )
	{
		anyID id = (*iter).first;
		TS3_VECTOR pos = (*iter).second;
		if ( previousData.clientPositions.count( id ) )
		{
			if ( previousData.clientPositions[id] != pos )
			{
				emit clientPositionChanged( id, pos );
			}
		}
		else
		{
			emit clientAdded( id, pos );
		}
	}
	for ( auto iter = previousData.clientPositions.cbegin(); iter != previousData.clientPositions.cend(); ++iter )
	{
		anyID id = (*iter).first;
		if ( !data.clientPositions.count( id ) )
		{
			emit clientRemoved( id );
		}
	}

	previousData = data;
}

bool SharedMemoryListener::connectToSharedMemory()
{
	if ( memory->create( 1024 ) == false )
	{
		if ( memory->error() == QSharedMemory::AlreadyExists )
		{
			return memory->attach();
		}
		return false;
	}
	return true;
}

