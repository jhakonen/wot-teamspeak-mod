# TessuMod: Mod for integrating TeamSpeak into World of Tanks
# Copyright (C) 2017  Janne Hakonen
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

from __future__ import absolute_import
import logging
import sys
import traceback

import BWLogging

class LogRedirectionHandler(logging.Handler):
	"""
	Specialized logging handler which redirects logging calls to BigWorld's
	logging facility. In a difference to BWLogging.BWLogRedirectionHandler this
	handles also exception information, printing it log output as well.
	"""

	def emit(self, record):
		category = record.name.encode(sys.getdefaultencoding())
		msg = record.getMessage()
		if record.exc_info is not None:
			msg += "\n" + "".join(traceback.format_exception(*record.exc_info))
		msg = msg.encode(sys.getdefaultencoding())
		BWLogging.logLevelToBigWorldFunction[record.levelno](category, msg, None)
