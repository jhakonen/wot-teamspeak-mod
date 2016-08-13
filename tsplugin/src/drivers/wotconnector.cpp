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

#include "wotconnector.h"
#include "../entities/vector.h"
#include "../utils/logging.h"

#include <QTimer>
#include <QSharedMemory>
#include <QDateTime>
#include <iostream>
#include <QIODevice>
#include <QDataStream>

namespace {

const int TIME_LIMIT = 5;
const quint8 PLUGIN_VERSION = 1;

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

class MemoryAreaBuffer : public QIODevice
{
public:
	MemoryAreaBuffer( QSharedMemory *memory, QObject *parent = 0 )
	: QIODevice( parent ), memoryData( memory->data() ), memorySize( memory->size() )
	{
	}

	void setMemoryArea( void* data, int size )
	{
		memoryData = data;
		memorySize = size;
	}

	virtual bool open( OpenMode mode )
	{
		return QIODevice::open( mode | Unbuffered );
	}

protected:
	virtual qint64 readData( char* data, qint64 maxSize )
	{
		if ( isOpen() )
		{
			qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
			memcpy( data, (char*)memoryData + pos(), size );
			return size;
		}
		return -1;
	}

	virtual qint64 writeData( const char* data, qint64 maxSize )
	{
		if ( isOpen() )
		{
			qint64 size = std::max( (qint64)0, std::min( memorySize - pos(), maxSize ) );
			memcpy( (char*)memoryData + pos(), data, size );
			return size;
		}
		return -1;
	}

private:
	void* memoryData;
	qint64 memorySize;
};

struct PositionalAudioData
{
	PositionalAudioData()
		: timestamp( 0 )
	{
	}

	quint32 timestamp;
	Entity::Vector cameraPosition;
	Entity::Vector cameraDirection;
	QMap<quint16, Entity::Vector> clientPositions;
};

QDataStream& operator>>( QDataStream &stream, Entity::Vector& vector )
{
	float x, y, z;
	stream >> x >> y >> z;
	vector.x = x;
	vector.y = y;
	vector.z = z;
	return stream;
}

QDataStream& operator>>( QDataStream &stream, PositionalAudioData& data )
{
	quint16 id;
	Entity::Vector position;
	quint8 clientCount;
	stream >> data.timestamp
		   >> data.cameraPosition
		   >> data.cameraDirection
		   >> clientCount;
	for( int i = 0; i < clientCount; i++ )
	{
		stream >> id >> position;
		data.clientPositions[id] = position;
	}
	return stream;
}

}

namespace Driver
{

class WotConnectorPrivate
{
public:
	WotConnectorPrivate( WotConnector *q )
		: memoryConnectTimer( new QTimer( q ) ), readMemoryTimer( new QTimer( q ) ),
		  positionalDataMemory( new QSharedMemory( q ) ), pluginInfoMemory( new QSharedMemory( q ) )
	{
	}

	void writePluginInfo()
	{
		if ( pluginInfoMemory->create( sizeof( PLUGIN_VERSION ) ) == false )
		{
			Log::error() << "Failed to create shared memory for plugin info, reason: " << pluginInfoMemory->errorString();
			return;
		}
		MemoryAreaBuffer buffer( pluginInfoMemory );
		if ( buffer.open( QIODevice::WriteOnly ) == false )
		{
			Log::error() << "Failed to open buffer";
			return;
		}
		MyDataStream stream( &buffer );
		stream << PLUGIN_VERSION;
	}

	QTimer* memoryConnectTimer;
	QTimer* readMemoryTimer;
	QSharedMemory* positionalDataMemory;
	QSharedMemory* pluginInfoMemory;
	MemoryAreaBuffer* memoryBuffer;
	PositionalAudioData previousData;
};

WotConnector::WotConnector( QObject *parent )
	: QObject( parent ), d_ptr( new WotConnectorPrivate( this ) )
{
	Q_D( WotConnector );
	connect( d->memoryConnectTimer, SIGNAL(timeout()), this, SLOT(connectToMemory()) );
	d->memoryConnectTimer->setInterval( 5000 );
	d->memoryConnectTimer->setSingleShot( false );
	connect( d->readMemoryTimer, SIGNAL(timeout()), this, SLOT(readMemory()) );
	d->readMemoryTimer->setInterval( 100 );
	d->readMemoryTimer->setSingleShot( false );
	d->positionalDataMemory->setNativeKey( "TessuModTSPlugin3dAudio" );
	d->pluginInfoMemory->setNativeKey( "TessuModTSPluginInfo" );
}

WotConnector::~WotConnector()
{
	Q_D( WotConnector );
	d->memoryConnectTimer->stop();
	d->readMemoryTimer->stop();
	delete d;
}

void WotConnector::initialize()
{
	Q_D( WotConnector );
	d->memoryConnectTimer->start();
	d->writePluginInfo();
}

QObject *WotConnector::qtObj()
{
	return this;
}

void WotConnector::connectToMemory()
{
	Q_D( WotConnector );
	if ( d->positionalDataMemory->attach( QSharedMemory::ReadOnly ) == false )
	{
		if ( d->positionalDataMemory->error() != QSharedMemory::NotFound )
		{
			Log::error() << "Failed to connect to positional audio shared memory, reason: " << d->positionalDataMemory->errorString();
		}
		return;
	}
	d->memoryBuffer = new MemoryAreaBuffer( d->positionalDataMemory, this );
	if ( d->memoryBuffer->open( QIODevice::ReadOnly ) == false )
	{
		Log::error() << "Failed to open buffer";
		return;
	}
	d->memoryConnectTimer->stop();
	d->readMemoryTimer->start();
}

void WotConnector::readMemory()
{
	Q_D( WotConnector );
	d->memoryBuffer->seek( 0 );
	MyDataStream stream( d->memoryBuffer );
	PositionalAudioData data;
	stream >> data;

	if( ( QDateTime::currentDateTime().toTime_t() - data.timestamp ) > TIME_LIMIT )
	{
		data.cameraPosition = Entity::Vector();
		data.cameraDirection = Entity::Vector();
		data.clientPositions.clear();
	}

	if( data.cameraPosition != d->previousData.cameraPosition )
	{
		emit gameCameraPositionChanged( data.cameraPosition );
	}
	if( data.cameraDirection != d->previousData.cameraDirection )
	{
		emit gameCameraDirectionChanged( data.cameraDirection );
	}
	foreach( quint16 id, data.clientPositions.keys() )
	{
		Entity::Vector pos = data.clientPositions[id];
		if ( d->previousData.clientPositions.contains( id ) )
		{
			if ( d->previousData.clientPositions[id] != pos )
			{
				emit gameUserPositionChanged( id, pos );
			}
		}
		else
		{
			emit gameUserAdded( id );
			emit gameUserPositionChanged( id, pos );
		}
	}
	foreach( quint16 id, d->previousData.clientPositions.keys() )
	{
		if ( !data.clientPositions.contains( id ) )
		{
			emit gameUserRemoved( id );
		}
	}

	d->previousData = data;
}

}
