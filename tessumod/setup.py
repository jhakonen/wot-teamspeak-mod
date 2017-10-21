#!/usr/bin/env python

from setuptools import setup, find_packages
import os

import setup_helpers

script_dir = os.path.dirname(__file__)
readme_path = os.path.join(script_dir, '..', 'README.md')

setup(
    name = 'tessumod',
    version = '0.7.0',
    description = 'Mod for integrating Teamspeak to World of Tanks',
    long_description = open(readme_path).read(),
    author = 'jhakonen',
    license = 'LGPL 2.1 License',
    url = 'http://forum.worldoftanks.eu/index.php?/topic/433614-/',
    packages = find_packages('src/scripts/client/gui/mods'),
    py_modules = ['mod_tessumod'],
    package_dir = {'':'src/scripts/client/gui/mods'},
    data_files = [
        'src/scripts/client/gui/mods/tessumod/config.json',
        'src/scripts/client/gui/mods/tessumod/assets/checkbox_on.png',
        'src/scripts/client/gui/mods/tessumod/assets/checkbox_off.png',
        'src/scripts/client/gui/mods/tessumod/assets/ts_notification_icon.png',
    ],
    cmdclass = {
        'build_py': setup_helpers.GenerateInFilesCommand,
    },
    setup_requires = ['wotdisttools'],
    # Required as wotdisttools is not yet in PyPI
    dependency_links = [
        'https://github.com/jhakonen/wotdisttools/tarball/master#egg=wotdisttools'
    ],
)
