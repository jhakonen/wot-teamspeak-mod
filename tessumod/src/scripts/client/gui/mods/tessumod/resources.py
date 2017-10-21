"""
This module contains helper function for retrieving files from within a wotmod
package. Function implementations are copied from packages specification
(see docs/packages_doc_0.6_en.pdf).

Licensed under WTFPL (see www.wtfpl.net).
"""

import ResMgr

def read_file(vfs_path, read_as_binary=True):
    """
    Reads a file from a wotmod package.

    :param vfs_path:       path within a package
    :param read_as_binary: read file in binary or text mode
    :return: file contents a string
    """
    vfs_file = ResMgr.openSection(vfs_path)
    if vfs_file is not None and ResMgr.isFile(vfs_path):
        if read_as_binary:
            return str(vfs_file.asBinary)
        else:
            return str(vfs_file.asString)
    return None

def list_directory(vfs_directory):
    """
    Returns list of elements in a directory within a wotmod package.

    :param vfs_directory: directory path within a package
    :return: list of elements
    """
    result = []
    folder = ResMgr.openSection(vfs_directory)
    if folder is not None and ResMgr.isDir(vfs_directory):
        for name in folder.keys():
            if name not in result:
                result.append(name)
    return sorted(result)

def file_copy(vfs_from, realfs_to):
    """
    Copies a file from within a wotmod package to a destination path in real
    file system.

    :param vfs_from: source file path within a wotmod package
    :param realfs_to: destination file path in real file system
    """
    realfs_directory = os.path.dirname(realfs_to)
    if not os.path.exists(realfs_directory):
        os.makedirs(realfs_directory)
    vfs_data = file_read(vfs_from)
    if vfs_data:
        with open(realfs_to, 'wb') as realfs_file:
            realfs_file.write(vfs_data)
