#!/usr/bin/env python3

from setuptools import setup, find_packages

import setup_helpers

setup(
    name = 'tessumod',
    description = 'Mod for integrating Teamspeak to World of Tanks',
    author = 'jhakonen',
    license = 'LGPL 2.1 License',
    url = 'http://forum.worldoftanks.eu/index.php?/topic/433614-/',
    use_scm_version={
        'version_scheme': 'post-release',
    },
    packages = find_packages('src'),
    py_modules = ['mod_tessumod'],
    package_dir = {'':'src'},
    data_files = [
        'data/checkbox_on.png',
        'data/checkbox_off.png',
        'data/ts_notification_icon.png',
        'data/tsplugin_install_notification.json',
        'data/tsplugin_update_notification.json',
    ],
    cmdclass = {
        'build_py': setup_helpers.GenerateInFilesCommand,
        'clean': setup_helpers.CleanCommand,
        'package': setup_helpers.PackageCommand
    },
    setup_requires = [
        'setuptools_scm==3.5.0',
        'pytest-runner==5.2',
        'setuptools-wotmod@git+https://github.com/jhakonen/setuptools-wotmod.git@master',
    ],
    tests_require = [
        'aiohttp==3.7.4',
        'pydash==4.7.6',
        'pytest==5.4.2',
        'pytest-asyncio==0.12.0',
        'pytest-pythonpath==0.7.3',
        'nose==1.3.7',
    ],
)
