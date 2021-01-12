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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
import textwrap

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv


from discord.ext import commands, tasks

from discord.ext.commands import Converter, CommandError

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

# from gidtools.gidfiles import (QuickFile, readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
#                                dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.named_tuples import FlagItem

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


class DateTimeFullConverter(Converter):
    def __init__(self):
        self.format = "%Y-%m-%d_%H-%M-%S"
        self.date_and_time_regex = re.compile(r'(?P<year>\d\d\d\d).*?(?P<month>[01]\d).*?(?P<day>[0123]\d).*?(?P<hour>[012]\d).*?(?P<minute>[0-6]\d).*?(?P<second>[0-6]\d)')

    async def convert(self, ctx, argument):
        result = self.date_and_time_regex.search(argument)
        if result is None:
            raise CommandError("wrong date and time format")
        result_dict = result.groupdict()
        new_argument = f"{result_dict.get('year')}-{result_dict.get('month')}-{result_dict.get('day')}_{result_dict.get('hour')}-{result_dict.get('minute')}-{result_dict.get('second')}"
        try:
            return datetime.strptime(new_argument, self.format)
        except Exception as error:
            raise CommandError(error)


class DateOnlyConverter(Converter):
    def __init__(self):
        self.format = "%Y-%m-%d"
        self.date_regex = re.compile(r'(?P<year>\d\d\d\d).*?(?P<month>[01]\d).*?(?P<day>[0123]\d)')

    async def convert(self, ctx, argument):
        result = self.date_regex.search(argument)
        if result is None:
            raise CommandError("wrong date and time format")
        result_dict = result.groupdict()
        new_argument = f"{result_dict.get('year')}-{result_dict.get('month')}-{result_dict.get('day')}"
        try:
            return datetime.strptime(new_argument, self.format)
        except Exception as error:
            raise CommandError(error)


class FlagArg(Converter):
    def __init__(self, available_flags):
        self.available_flags = available_flags

    async def convert(self, ctx, argument):
        if argument.startswith('--'):
            name = argument.removeprefix('--').replace('-', '_').lower()
            if name in self.available_flags:
                return name
            else:
                raise CommandError
        else:
            raise CommandError


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
