# region[Imports]

import os
import sys
from inspect import getmembers, isclass, isfunction
from typing import Union, Dict, Set, List, Tuple
from os import PathLike
import json

# endregion [Imports]


def pathmaker(first_segment, *in_path_segments, rev=False):
    """
    Normalizes input path or path fragments, replaces '\\' with '/' and combines fragments.

    Parameters
    ----------
    first_segment : str
        first path segment, if it is 'cwd' gets replaced by 'os.getcwd()'
    rev : bool, optional
        If 'True' reverts path back to Windows default, by default None

    Returns
    -------
    str
        New path from segments and normalized.
    """

    _path = first_segment

    _path = os.path.join(_path, *in_path_segments)
    if rev is True or sys.platform not in ['win32', 'linux']:
        return os.path.normpath(_path)
    return os.path.normpath(_path).replace(os.path.sep, '/')


def writejson(in_object, in_file, sort_keys=True, indent=4, **kwargs):
    with open(in_file, 'w') as jsonoutfile:
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent, **kwargs)


def bytes2human(n, annotate=False):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('Kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Zb', 'Yb')
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    for s in reversed(symbols):
        if n >= prefix[s]:
            _out = float(n) / prefix[s]
            if annotate is True:
                _out = '%.1f %s' % (_out, s)
            return _out
    _out = n
    if annotate is True:
        _out = "%s b" % _out
    return _out


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

ANTISTASI_FOLDER_PATH = os.path.join(THIS_FILE_DIR, '..')
ANTISTASI_FOLDER_PATH = os.path.join(r"D:\Dropbox\hobby\Modding\Programs\Github\Foreign_Repos\A3-Antistasi")
# FILE_TO_EXCLUDE = set(map(lambda x: x.casefold(), ['.gitattributes', '.gitignore', '.travis.yml']))
# FOLDER_TO_EXCLUDE = set(map(lambda x: x.casefold(), ['.git', 'upsmon']))
OUTPUT_NAME = 'repo_file_index.json'
OUTPUT_FILE = OUTPUT_NAME


class AntistasiFile:

    def __init__(self, file_path: Union[str, PathLike]) -> None:
        self.full_path = file_path
        self.path = os.path.relpath(self.full_path, ANTISTASI_FOLDER_PATH)
        self.full_name = os.path.basename(self.full_path)
        self.name, self.extension = os.path.splitext(self.full_name)

    @property
    def stat_object(self) -> os.stat_result:
        return os.stat(self.full_path)

    @property
    def size(self):
        return self.stat_object.st_size

    # @property
    # def pretty_size(self):
    #     return bytes2human(self.size, True)

    def dump(self):
        _out = {}
        for name, _object in getmembers(self):

            if all([not name.startswith('_'), not name.endswith('_'), name not in {'dump', 'stat_object', 'full_path'}]):
                _out[name] = _object if _object else None
        return _out


def walk_files():
    for dirname, folderlist, filelist in os.walk(ANTISTASI_FOLDER_PATH, topdown=True):

        if '.git' in folderlist:
            folderlist.remove('.git')
        for file in filelist:
            path = os.path.join(dirname, file)
            yield AntistasiFile(path)


def main():
    writejson([item.dump() for item in walk_files()], OUTPUT_FILE)


if __name__ == '__main__':
    main()
