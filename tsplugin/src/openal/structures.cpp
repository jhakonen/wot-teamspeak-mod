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

#include "structures.h"

namespace OpenAL {

OutputInfo::OutputInfo()
	: valid( false )
{
}

OutputInfo::OutputInfo( const QString &deviceName, quint32 sampleRate, bool hrtfEnabled )
	: valid( true ), deviceName( deviceName ), sampleRate( sampleRate ), hrtfEnabled( hrtfEnabled )
{
}

bool OutputInfo::isValid() const
{
	return valid;
}

const QString &OutputInfo::getDeviceName() const
{
	return deviceName;
}

quint32 OutputInfo::getSampleRate() const
{
	return sampleRate;
}

bool OutputInfo::isHrtfEnabled() const
{
	return hrtfEnabled;
}

bool OutputInfo::operator<( const OutputInfo &other ) const
{
	return deviceName < other.deviceName &&
			sampleRate < other.sampleRate &&
			hrtfEnabled < other.hrtfEnabled;
}

bool OutputInfo::operator==( const OutputInfo &other ) const
{
	return deviceName == other.deviceName &&
			sampleRate == other.sampleRate &&
			hrtfEnabled == other.hrtfEnabled;
}

bool OutputInfo::operator!=( const OutputInfo &other ) const
{
	return !operator==( other );
}

SourceInfo::SourceInfo()
	: valid( false )
{

}

SourceInfo::SourceInfo( const OutputInfo &outputInfo,
						quint32 id,
						const Entity::Vector &position,
						qreal rolloffFactor,
						bool relative,
						bool streaming )
	: valid( true ), id( id ), outputInfo( outputInfo ), position( position ),
	  rolloffFactor( rolloffFactor ), relative( relative ),
	  streaming( streaming )
{
}

bool SourceInfo::isValid() const
{
	return valid && outputInfo.isValid();
}

const OutputInfo &SourceInfo::getOutputInfo() const
{
	return outputInfo;
}

quint32 SourceInfo::getId() const
{
	return id;
}

const Entity::Vector &SourceInfo::getPosition() const
{
	return position;
}

qreal SourceInfo::getRolloffFactor() const
{
	return rolloffFactor;
}

bool SourceInfo::isRelative() const
{
	return relative;
}

bool SourceInfo::isStreaming() const
{
	return streaming;
}

ListenerInfo::ListenerInfo()
	: valid( false ), gain( 0 )
{

}

ListenerInfo::ListenerInfo( const OutputInfo &outputInfo,
							const Entity::Vector &forward,
							const Entity::Vector &up,
							const Entity::Vector &velocity,
							const Entity::Vector &position,
							qreal gain )
	: valid( true ), outputInfo( outputInfo ), forward( forward ), up( up ),
	  velocity( velocity ), position( position ), gain( gain )
{
}

bool ListenerInfo::isValid() const
{
	return valid && outputInfo.isValid();
}

const OutputInfo &ListenerInfo::getOutputInfo() const
{
	return outputInfo;
}

const Entity::Vector &ListenerInfo::getForward() const
{
	return forward;
}

const Entity::Vector &ListenerInfo::getUp() const
{
	return up;
}

const Entity::Vector &ListenerInfo::getVelocity() const
{
	return velocity;
}

const Entity::Vector &ListenerInfo::getPosition() const
{
	return position;
}

qreal ListenerInfo::getGain() const
{
	return gain;
}

AudioData::AudioData( quint8 channelCount,
					  quint8 sampleSize,
					  quint32 dataSize,
					  quint32 sampleRate,
					  const void *data )
	: channelCount( channelCount ), sampleSize( sampleSize ),
	  dataSize( dataSize ), sampleRate( sampleRate ), data( data )
{
}

quint8 AudioData::getChannelCount() const
{
	return channelCount;
}

quint8 AudioData::getSampleSize() const
{
	return sampleSize;
}

quint32 AudioData::getDataSize() const
{
	return dataSize;
}

quint32 AudioData::getSampleRate() const
{
	return sampleRate;
}

const void *AudioData::getData() const
{
	return data;
}

}
