"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserDict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

# import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

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

import gidlogger as glog

from antipetros_discordbot.utility.gidtools_functions import (readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
                                                              dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]


# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
from antipetros_discordbot.utility.misc import date_today, async_date_today
# endregion[Constants]


class CommandStatDict(UserDict):
    overall_data_file = pathmaker(APPDATA['stats'], "overall_invoked_stats.json")

    def __init__(self, file: str, default_content_function: Callable):
        self.file = pathmaker(file)
        super().__init__({})
        self.default_content_function = default_content_function
        self.default_content = None
        self.last_initialized = None
        self.load_data()

    @property
    def is_empty(self):
        return self.data == {}

    @property
    def sum_data(self):
        _out = {'overall': {'successful': sum(value.get('successful') for key, value in self.data['overall'].items()),
                            'unsuccessful': sum(value.get('unsuccessful') for key, value in self.data['overall'].items())}}

        for date, value in self.data.items():
            if date != 'overall':
                _out[date] = {'successful': sum(value.get('successful') for key, value in self.data[date].items()),
                              'unsuccessful': sum(value.get('unsuccessful') for key, value in self.data[date].items())}
        return _out

    def initialize_data(self):
        self.default_content = list(set(self.default_content_function()))
        if 'overall' not in self.data:
            self.data['overall'] = {}
        if date_today() not in self.data:
            self.data[date_today()] = {}
        for item in self.default_content:
            if item not in self.data['overall']:
                self.data['overall'][item] = {'successful': 0, 'unsuccessful': 0}
            if item not in self.data[date_today()]:
                self.data[date_today()][item] = {'successful': 0, 'unsuccessful': 0}
        self.last_initialized = datetime.utcnow()

    def add_tick(self, key, unsuccessful=False):
        if key is None or key == 'None':
            return
        if self.last_initialized + timedelta(days=1) <= datetime.utcnow():
            self.save_data()
            self.initialize_data()

        typus = 'unsuccessful' if unsuccessful is True else "successful"
        self.data['overall'][key][typus] += 1
        self.data[date_today()][key][typus] += 1

    def load_data(self):
        if os.path.isfile(self.file) is False:
            self.initialize_data()
            self.save_data()
        self.data = loadjson(self.file)
        self.initialize_data()

    def save_data(self):
        writejson(self.data, self.file)

    def save_overall(self):
        writejson(self.sum_data, self.overall_data_file)


# region[Main_Exec]

if __name__ == '__main__':
    pass
# endregion[Main_Exec]
