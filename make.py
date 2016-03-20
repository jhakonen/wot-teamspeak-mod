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

import sys
import os
import json

# prevent *.pyc-file generation
sys.dont_write_bytecode = True # for current process
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" # for subprocesses

from invoke import ctask as task, Program, Argument, Config, Collection
from termcolor import colored

from tools import make_tools

root = os.path.dirname(os.path.realpath(__file__))

class Make(Program):

	def core_args(self):
		core_args = super(Make, self).core_args()
		extra_args = [
			Argument(names=('verbose', 'v'), help="Enable verbose output from subcommands", default=False, kind=bool),
			Argument(names=('exclude-tags',), help="Exclude builders which have given tags (comma separated list)", default=""),
			Argument(names=('list',), help="HACK", default=False, kind=bool),
			Argument(names=('no-dedupe',), help="HACK", default=False, kind=bool)
		]
		return core_args + extra_args

class MakeConfig(Config):

	def __init__(
		self,
		defaults=None,
		overrides=None,
		system_prefix=None,
		user_prefix=None,
		project_home=None,
		env_prefix=None,
		runtime_path=None
	):
		overrides["verbose"] = program.args.verbose.value
		overrides["exclude-tags"] = [tag.strip() for tag in program.args["exclude-tags"].value.split(",")]
		configure_path = os.path.join(os.getcwd(), "config.json")
		if os.path.exists(configure_path):
			runtime_path = configure_path
		
		super(MakeConfig, self).__init__(
			defaults=defaults,
			overrides=overrides,
			system_prefix=system_prefix,
			user_prefix=user_prefix,
			project_home=project_home,
			env_prefix=env_prefix,
			runtime_path=runtime_path
		)

@task
def configure(ctx, qmake_x86=None, qmake_x64=None, msvc_vars=None, wot_install=None):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Configuring... ", lb_end=False)
	try:
		with open("config.json", "w+") as file:
			contents = file.read()
			config = {"vars": {}}
			if contents:
				config = json.loads(contents)
			if qmake_x86:
				config["vars"]["qmake_path_x86"] = qmake_x86
			if qmake_x64:
				config["vars"]["qmake_path_x64"] = qmake_x64
			if msvc_vars:
				config["vars"]["msvc_vars_path"] = msvc_vars
			if wot_install:
				config["vars"]["wot_install_path"] = wot_install
			file.write(json.dumps(config))
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task
def build(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Building... ", lb_end=False)
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in builders:
				if "build" in builder.tags:
					builder.execute()
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task
def clean(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Cleaning... ", lb_end=False)
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in reversed(builders):
				if "clean" in builder.tags:
					builder.clean()
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task
def unittests(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Running unit tests... ", lb_end=False)
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in builders:
				if "unittests" in builder.tags:
					builder.execute()
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task
def futes(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Running functional tests... ", lb_end=False)
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in builders:
				if "futes" in builder.tags:
					builder.execute()
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task(unittests, futes)
def tests(ctx):
	pass

@task(build)
def install(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Installing... ", lb_end=False)
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in builders:
				if "install" in builder.tags:
					builder.execute()
	except:
		logger.exception()
		sys.exit(1)
	else:
		logger.info(colored("[ ok ]", "green"), lb_start=False)

@task(build, tests)
def release(ctx):
	pass

@task
def tail(ctx):
	logger = make_tools.Logger(verbose=ctx.verbose)
	logger.info("Tailing python.log...")
	try:
		with make_tools.with_builders(logger, root, ctx.config, ctx["exclude-tags"]) as builders:
			for builder in builders:
				if "tail" in builder.tags:
					builder.execute()
	except:
		logger.exception()
		sys.exit(1)

ns = Collection(loaded_from=root)
ns.add_task(configure)
ns.add_task(clean)
ns.add_task(build)
ns.add_task(install)
ns.add_task(tests)
ns.add_task(unittests)
ns.add_task(futes)
ns.add_task(release)
ns.add_task(tail)

program = Make(version="1.0.0", name="Make", binary="make.py", namespace=ns, config_class=MakeConfig)

if __name__ == "__main__":
	program.run()
