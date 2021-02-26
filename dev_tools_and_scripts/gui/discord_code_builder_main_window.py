"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import os
import re
import sys
import json
import lzma
import time
import queue
import base64
import pickle
import random
import shelve
import shutil
import asyncio
import logging
import sqlite3
import platform
import importlib
import subprocess
import unicodedata
from io import BytesIO
from abc import ABC, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor, QCursor, QPixmap, QStandardItem, QRegExpValidator
from PyQt5.QtCore import Qt, QRect, QSize, QObject, QRegExp, QThread, QMetaObject, QCoreApplication, QFileSystemWatcher, QPropertyAnimation, QAbstractTableModel, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QMenu, QFrame, QLabel, QAction, QDialog, QLayout, QWidget, QWizard, QMenuBar, QSpinBox, QCheckBox, QComboBox, QGroupBox, QLineEdit, QListView, QCompleter, QStatusBar,
                             QTableView, QTabWidget, QDockWidget, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QListWidget, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
                             QSpacerItem, QToolButton, QVBoxLayout, QWizardPage, QApplication, QButtonGroup, QRadioButton, QFontComboBox, QStackedWidget, QListWidgetItem, QSystemTrayIcon,
                             QTreeWidgetItem, QDialogButtonBox, QAbstractItemView, QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator)

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.file_system_walk import FileSystemWalkerItem, filesystem_walker, filesystem_walker_files, filesystem_walker_folders
from antipetros_discordbot.utility.gidtools_functions import (readit, clearit, readbin, work_in, writeit, loadjson, pickleit, splitoff, writebin, pathmaker, writejson, dir_change,
                                                              linereadit, bytes2human, create_file, file_walker, get_pickled, ishash_same, ext_splitter, appendwriteit, create_folder,
                                                              number_rename, timenamemaker, cascade_rename, file_name_time, absolute_listdir, hash_to_solidcfg, path_part_remove,
                                                              from_dict_to_file, get_absolute_path, file_name_modifier, limit_amount_of_files, limit_amount_files_absolute)

from antipetros_discordbot.dev_tools_and_scripts.gui.converted_designer_files.Ui_discord_code_builder_mainwindow import Ui_DiscordCodeBuilderMainWindow
from antipetros_discordbot.dev_tools_and_scripts.gui.converted_designer_files.Ui_discord_code_builder_main_selection_screen import Ui_MainSelectionScreen
from antipetros_discordbot.dev_tools_and_scripts.gui.converted_designer_files.Ui_discord_code_builder_cog_builder import Ui_CogBuilder
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class MainSelectionScreen(Ui_MainSelectionScreen, QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        super().setupUi(self)


class DiscordCodeBuilderMainWindow(Ui_DiscordCodeBuilderMainWindow, QMainWindow):

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().setupUi(self)
        self.app = app
        self.main_selection_screen = MainSelectionScreen()
        self.gridLayout_2.addWidget(self.main_selection_screen)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    main_window = DiscordCodeBuilderMainWindow(app)
    main_window.show()
    # main_window.add_systemtray(SystemTray)
    sys.exit(app.exec_())

# region[Main_Exec]


if __name__ == '__main__':
    try:
        main()
    except:
        log.exception(sys.exc_info()[0])
        raise


# endregion[Main_Exec]
