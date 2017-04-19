# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2016  Janne Hakonen
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import time
import traceback

class LOG_LEVEL(object):
	DEBUG = 0
	NOTE = 1
	WARNING = 2
	ERROR = 3

CURRENT_LOG_LEVEL = LOG_LEVEL.NOTE

def install_logger_impl(impl):
	global LOG_DEBUG, LOG_DEBUG, LOG_NOTE, LOG_WARNING, LOG_ERROR, LOG_CURRENT_EXCEPTION
	LOG_DEBUG = impl.debug
	LOG_NOTE = impl.note
	LOG_WARNING = impl.warning
	LOG_ERROR = impl.error
	LOG_CURRENT_EXCEPTION = impl.exception

def LOG_DEBUG(msg, *args):
	print msg

def LOG_NOTE(msg, *args):
	print msg

def LOG_WARNING(msg, *args):
	print msg

def LOG_ERROR(msg, *args):
	print msg

def LOG_CURRENT_EXCEPTION():
	print traceback.format_exc()

def prefix_with_timestamp(msg):
	if CURRENT_LOG_LEVEL <= LOG_LEVEL.DEBUG:
		return time.strftime("[%H:%M:%S]") + " " + msg
	return msg
