#!/usr/bin/env python

from setuptools import setup, find_packages
import os

import setup_helpers

setup(
    name = 'tessumod',
    version = '0.7.1',
    description = 'Mod for integrating Teamspeak to World of Tanks',
    author = 'jhakonen',
    license = 'LGPL 2.1 License',
    url = 'http://forum.worldoftanks.eu/index.php?/topic/433614-/',
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
    setup_requires = ['setuptools-wotmod', 'nose>=1.0'],
    # Required as setuptools-wotmod is not yet in PyPI
    dependency_links = [
        'https://github.com/jhakonen/setuptools-wotmod/tarball/0.2.0#egg=setuptools-wotmod'
    ],
    test_suite = 'nose.collector'
)
