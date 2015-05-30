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

#include "wavfile.h"
#include <QFile>
#include <QDataStream>
#include <QByteArray>

namespace
{

const int TAG_UNCOMPRESSED_PCM = 0x1;
const char* RIFF_CONTAINER_TYPE = "RIFF";
const char* WAVE_MEDIA_TYPE = "WAVE";
const char* FORMAT_TOKEN = "fmt ";
const char* DATA_TOKEN = "data";

}

WavFile::WavFile( const QString &fileName, QObject *parent )
	: QIODevice( parent ), file( new QFile( fileName, parent ) )
{
}

WavFile::~WavFile()
{
	close();
}


bool WavFile::isSequential() const
{
	return false;
}

bool WavFile::open( OpenMode mode )
{
	if( mode & WriteOnly )
	{
		setErrorString( "Writing is not supported" );
		return false;
	}

	if( !file->open( mode ) )
	{
		setErrorString( file->errorString() );
		return false;
	}

	QByteArray containerType( 4, 0 );
	QByteArray mediaType( 4, 0 );
	QByteArray formatToken( 4, 0 );
	QByteArray dataToken( 4, 0 );
	quint32 fileSize;
	quint32 formatHeaderSize;
	quint16 formatTag;
	quint32 bytesPerSecond;
	quint16 blockAlignment;

	QDataStream stream( file );
	stream.setByteOrder( QDataStream::LittleEndian );

	stream.readRawData( containerType.data(), containerType.size() );
	if( containerType != RIFF_CONTAINER_TYPE )
	{
		setErrorString( "File is not in Microsoft RIFF format" );
		file->close();
		return false;
	}

	stream >> fileSize;

	stream.readRawData( mediaType.data(), mediaType.size() );
	if( mediaType != WAVE_MEDIA_TYPE )
	{
		setErrorString( "File is not a WAVE file" );
		file->close();
		return false;
	}

	stream.readRawData( formatToken.data(), formatToken.size() );
	if( formatToken != FORMAT_TOKEN )
	{
		setErrorString( "Format chunk start indication token missing" );
		file->close();
		return false;
	}

	stream >> formatHeaderSize;

	if( formatHeaderSize != 16 )
	{
		setErrorString( QString( "Unsupported header size (size: %1)" ).arg( formatHeaderSize ) );
		file->close();
		return false;
	}

	stream >> formatTag;
	if( formatTag != TAG_UNCOMPRESSED_PCM )
	{
		setErrorString( "Only uncompressed PCM audio supported" );
		file->close();
		return false;
	}

	stream >> channelCount;
	stream >> sampleRate;
	stream >> bytesPerSecond;
	stream >> blockAlignment;
	stream >> bitsPerSample;

	stream.readRawData( dataToken.data(), dataToken.size() );
	if( dataToken != DATA_TOKEN )
	{
		setErrorString( "Data start indication token missing" );
		file->close();
		return false;
	}

	stream >> contentSize;
	contentStartPos = file->pos();

	return QIODevice::open( mode );
}

void WavFile::close()
{
	file->close();
}

quint16 WavFile::getChannels() const
{
	return channelCount;
}

quint32 WavFile::getSampleRate() const
{
	return sampleRate;
}

quint16 WavFile::getBitsPerSample() const
{
	return bitsPerSample;
}

qint64 WavFile::readData( char *data, qint64 maxlen )
{
	quint32 contentPos = file->pos() - contentStartPos;
	qint64 dataLeft = contentSize - contentPos;
	quint32 maxLength = std::min( maxlen, dataLeft );
	return file->read( data, maxLength );
}

qint64 WavFile::writeData( const char *data, qint64 len )
{
	Q_UNUSED( data );
	Q_UNUSED( len );
	throw std::runtime_error( "Not implemented" );
}
