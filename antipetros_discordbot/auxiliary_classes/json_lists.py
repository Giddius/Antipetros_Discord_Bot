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
from typing import Union, Any, List, Dict, Set, Tuple
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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserList
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

# from gidtools.gidfiles import (readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
#                                dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker

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


class AbstractJsonList(UserList, ABC):

    def __init__(self, json_file, serializer=None, default_value: list = None) -> None:
        self.default_value = [] if default_value is None else default_value
        self.file = self._validate_create_file(json_file)
        self.serializer = serializer

    @property
    @abstractmethod
    def data(self):
        ...

    @abstractmethod
    def _load(self):
        ...

    @abstractmethod
    def _write(self, in_data):
        ...

    @abstractmethod
    def append(self, item: Any):
        ...

    @abstractmethod
    def remove(self, item: Any):
        ...

    def _validate_create_file(self, json_file) -> str:
        if not json_file.endswith('.json'):
            raise TypeError(f"json_file needs to have the extension '.json' and not '{'.'+json_file.split('.')[-1]}'")
        if not os.path.exists(json_file):
            writejson(self.default_value, json_file)
        elif not isinstance(loadjson(json_file), list):
            raise TypeError(f"{self} can only be used with json data in List for and not {type(loadjson(json_file))}")
        return pathmaker(json_file)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(json_file={self.file}, serializer={self.serializer}, default_value={self.default_value})"


class JsonListImposter(AbstractJsonList):
    def __init__(self, json_file, serializer=None, default_value: list = None) -> None:
        super().__init__(json_file, serializer, default_value=default_value)

    @property
    def data(self):
        return self._load()

    def append(self, item: Any):
        stored_data = self._load()
        stored_data.append(item)
        self._write(stored_data)

    def _load(self):
        raw_data = loadjson(self.file)
        if self.serializer is None:
            return raw_data
        return self.serializer.deserialize(raw_data)

    def _write(self, in_data):
        in_data = in_data if self.serializer is None else self.serializer.serialize(in_data)
        writejson(in_data, self.file)

    def remove(self, item: Any):
        stored_data = self._load()
        stored_data.remove(item)
        self._write(stored_data)


class JsonSyncedList(AbstractJsonList):
    def __init__(self, json_file, serializer, default_value: list) -> None:
        super().__init__(json_file, serializer, default_value=default_value)

        # region[Main_Exec]


if __name__ == '__main__':
    x = JsonListImposter('test.json')

# endregion[Main_Exec]