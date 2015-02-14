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

#include <QIODevice>

class QFile;

/**
 * The WavFile class provides reading of wav-files.
 *
 * Implementation based on Nathan Davidson's tutorial at:
 *     http://www.gamedev.net/page/resources/_/technical/game-programming/loading-a-wave-file-r709
 */
class WavFile : public QIODevice
{
	Q_OBJECT

public:
	WavFile( const QString &fileName, QObject *parent = 0 );
	~WavFile();

public:
	// from QIODevice
	bool isSequential() const;
	bool open( OpenMode mode );
	void close();

	quint16 getChannels() const;
	quint32 getSampleRate() const;
	quint16 getBitsPerSample() const;

protected:
	// from QIODevice
	qint64 readData( char *data, qint64 maxlen );
	qint64 writeData( const char *data, qint64 len );

private:
	QFile *file;
	quint16 channelCount;
	quint32 sampleRate;
	quint16 bitsPerSample;
	quint32 contentSize;
	quint32 contentStartPos;
};
