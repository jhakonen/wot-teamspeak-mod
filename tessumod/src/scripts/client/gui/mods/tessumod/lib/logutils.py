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

import logging
import logging.config
from functools import wraps
from inspect import getcallargs
import os

logger = logging.getLogger("tessumod")

def trace_call(logger, level=logging.DEBUG):
	"""
	This decorator function writes to log when the decorated function is called.
	The log line contains method's name and arguments passed to it.
	"""
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			args_dict = getcallargs(func, *args, **kwargs)
			args_dict.pop("self", None)
			args_str = ", ".join([key+"="+repr(value) for key, value in args_dict.iteritems()])
			logger.log(level, func.__name__ + "(" + args_str + ")")
			return func(*args, **kwargs)
		return wrapper
	return decorator

def init(config_path, log_handler):
	global logger
	if os.path.exists(config_path):
		logging.config.fileConfig(config_path, disable_existing_loggers=False)
	logger.addHandler(log_handler)
	logger.propagate = False
