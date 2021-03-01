
"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

# * Standard Library Imports ---------------------------------------------------------------------------->
# * Standard Library Imports -->
import os
import sys
import shutil
from typing import Iterable, Union
from collections import namedtuple

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

# import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup


try:
    # * Third Party Imports -->
    # * Third Party Imports --------------------------------------------------------------------------------->
    import dotenv
except ImportError:
    os.system('pip install python-dotenv')
    # * Third Party Imports -->
    # * Third Party Imports --------------------------------------------------------------------------------->
    import dotenv

# from discord import Embed, File

# from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * PyQt5 Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

# from PyQt5.QtGui import QFont, QIcon, QBrush, QColor, QCursor, QPixmap, QStandardItem, QRegExpValidator

# from PyQt5.QtCore import (Qt, QRect, QSize, QObject, QRegExp, QThread, QMetaObject, QCoreApplication,
#                           QFileSystemWatcher, QPropertyAnimation, QAbstractTableModel, pyqtSlot, pyqtSignal)

# from PyQt5.QtWidgets import (QMenu, QFrame, QLabel, QAction, QDialog, QLayout, QWidget, QWizard, QMenuBar, QSpinBox, QCheckBox, QComboBox, QGroupBox, QLineEdit,
#                              QListView, QCompleter, QStatusBar, QTableView, QTabWidget, QDockWidget, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout,
#                              QHeaderView, QListWidget, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWizardPage,
#                              QApplication, QButtonGroup, QRadioButton, QFontComboBox, QStackedWidget, QListWidgetItem, QSystemTrayIcon, QTreeWidgetItem,
#                              QDialogButtonBox, QAbstractItemView, QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator)


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->


# from antipetros_discordbot.utility.gidtools_functions import ( readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
#                                dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]


# endregion[Logging]

# region [Constants]


dotenv.load_dotenv(dotenv.find_dotenv("_project_devmeta.env"))
TO_DELETE_FOLDER = ['logs', 'reports', 'dist', 'pyinstaller_output']
EXCLUDE_FOLDER = ['.git', 'init_userdata']


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]




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


def pathmaker(first_segment, *in_path_segments, rev=False):
    """
    Normalizes input path or path fragments, replaces '\\\\' with '/' and combines fragments.

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


class FileSystemWalkerItem(namedtuple('WalkerItem', ['name', 'path'])):
    byte = "byte"
    kilobyte = 'kilobyte'
    megabyte = 'megabyte'
    gigabyte = 'gigabyte'
    terrabyte = 'terrabyte'
    sgf = 1024  # SIZE_GENERAL_FACTOR
    size_conv = {'byte': {'factor': sgf**0, 'short_name': 'b'},
                 'kilobyte': {'factor': sgf**1, 'short_name': 'kb'},
                 'megabyte': {'factor': sgf**2, 'short_name': 'mb'},
                 'gigabyte': {'factor': sgf**3, 'short_name': 'gb'},
                 'terrabyte': {'factor': sgf**4, 'short_name': 'tb'}}

    def is_file(self):
        return os.path.isfile(self.path)

    def is_dir(self):
        return os.path.isdir(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def _size(self):
        if self.is_file() is True:
            size_b = os.stat(self.path).st_size
        else:
            size_b = 0
            for dirname, folderlist, filelist in os.walk(self.path):
                for file in filelist:
                    full_path = pathmaker(dirname, file)
                    size_b += os.stat(full_path).st_size

        return size_b

    def _converted_size(self, target_unit):
        return round(self._size() / self.size_conv.get(target_unit).get('factor'), ndigits=3)

    @property
    def size_b(self):
        return self._converted_size('byte')

    @property
    def size_kb(self):
        return self._converted_size('kilobyte')

    @property
    def size_mb(self):
        return self._converted_size('megabyte')

    @property
    def size_gb(self):
        return self._converted_size('gigabyte')

    @property
    def size_tb(self):
        return self._converted_size('terrabyte')

    @property
    def pretty_size(self):
        return bytes2human(self._size(), annotate=True)

    @property
    def ext(self):
        return os.path.splitext(self.name)[1].replace('.', '')

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    def delete(self, are_you_sure: bool = False):
        if are_you_sure is False:
            raise AssertionError
        if self.is_file() is True or os.scandir(self.path) == []:
            os.remove(self.path)
        elif self.is_dir() is True and os.scandir(self.path) != []:
            shutil.rmtree(self.path)

    def __str__(self):
        return pathmaker(self.path)


def _input_handle_excludes(value, typus="folder"):
    _standard_exclude_folders = ['.git', '.venv', '__pychache__', '.vscode']
    _standard_exclude_files = []
    _standard_exludes = _standard_exclude_folders if typus == 'folder' else _standard_exclude_files
    to_exclude = [] if value is None else value
    if to_exclude == 'standard':
        to_exclude = _standard_exludes
    if 'standard' in to_exclude:
        to_exclude.remove('standard')
        to_exclude += _standard_exludes
    return list(set(map(lambda x: x.casefold(), to_exclude)))


def filesystem_walker(start_folder, exclude_folder: Union[str, Iterable] = None, exclude_files: Union[str, Iterable] = None):
    folders_to_exclude = _input_handle_excludes(exclude_folder, typus='folder')
    files_to_exclude = _input_handle_excludes(exclude_files, typus='files')

    for dirname, folderlist, filelist in os.walk(start_folder):
        if all(exc_folder not in dirname.casefold() for exc_folder in folders_to_exclude):
            for file in filelist:
                if file not in files_to_exclude:
                    file_path = pathmaker(dirname, file)
                    yield FileSystemWalkerItem(file, file_path)
            for folder in folderlist:
                if folder not in folders_to_exclude:
                    folder_path = pathmaker(dirname, folder)
                    yield FileSystemWalkerItem(folder, folder_path)


def filesystem_walker_files(start_folder, exclude_folder: Union[str, Iterable] = None, exclude_files: Union[str, Iterable] = None):
    for item in filesystem_walker(start_folder, exclude_folder, exclude_files):
        if item.is_file() is True:
            yield item


def filesystem_walker_folders(start_folder, exclude_folder: Union[str, Iterable] = None, exclude_files: Union[str, Iterable] = None):
    for item in filesystem_walker(start_folder, exclude_folder, exclude_files):
        if item.is_dir() is True:
            yield item


def get_to_delete_folder():
    for folder in filesystem_walker_folders(os.getcwd(), exclude_folder='standard', exclude_files='standard'):
        if folder.name in TO_DELETE_FOLDER and all(excl_folder.casefold() not in folder.path.casefold() for excl_folder in EXCLUDE_FOLDER):
            yield folder


def recursively_delete_folder():
    for folder in get_to_delete_folder():
        print(f'deleting folder "{folder.path}"')
        folder.delete(True)


def dry_run():
    for folder in get_to_delete_folder():
        print(folder.path)


if __name__ == '__main__':
    input_data = '' if len(sys.argv) == 1 else sys.argv[1]
    if os.path.isdir(input_data) is True:
        print(f"changing dir to {input_data}")
        os.chdir(input_data)
    else:
        os.chdir(pathmaker(THIS_FILE_DIR, '../'))

    recursively_delete_folder()
