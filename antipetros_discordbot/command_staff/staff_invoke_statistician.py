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
from antipetros_discordbot.abstracts.command_staff_abstract import CommandStaffSoldierBase
from antipetros_discordbot.utility.named_tuples import InvokedCommandsDataItem
from antipetros_discordbot.utility.misc import date_today, async_date_today
from antipetros_discordbot.command_staff.helper.command_stats_dict import CommandStatDict
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class InvokeStatistician(CommandStaffSoldierBase):
    save_folder = APPDATA['stats']
    cog_invoked_stats_file = pathmaker(save_folder, 'cog_invoked_stats.json')
    command_invoked_stats_file = pathmaker(save_folder, 'command_invoked_stats.json')

    def __init__(self, bot, command_staff):
        self.bot = bot
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.command_staff = command_staff
        self.cog_invoked_stats = None
        self.command_invoked_stats = None
        self.stats_holder = None
        glog.class_init_notification(log, self)
        self.after_action()

    def cog_name_list(self):
        return [str(cog_object) for cog_name, cog_object in self.bot.cogs.items()]

    def command_name_list(self):
        return [command.name for command in self.bot.all_cog_commands()] + [self.bot.help_invocation]

    async def if_ready(self):
        if self.stats_holder is None:
            self.stats_holder = []
            if self.cog_invoked_stats is not None and self.cog_invoked_stats.is_empty is False:
                self.cog_invoked_stats.save_data()
            if self.command_invoked_stats is not None and self.command_invoked_stats.is_empty is False:
                self.command_invoked_stats.save_data()
                self.command_invoked_stats.save_overall()
            self.cog_invoked_stats = CommandStatDict(self.cog_invoked_stats_file, self.cog_name_list)
            self.command_invoked_stats = CommandStatDict(self.command_invoked_stats_file, self.command_name_list)
            self.stats_holder.append(self.cog_invoked_stats)
            self.stats_holder.append(self.command_invoked_stats)
            log.debug("'%s' command staff soldier was READY", str(self))

    async def get_todays_invoke_data(self):
        overall_data = self.command_invoked_stats.sum_data.get(date_today())
        data = '\n'.join(f"**{key}**: *{str(value)}*" for key, value in overall_data.items() if value != 0)
        overall_item = InvokedCommandsDataItem('overall', await async_date_today(), data)

        cogs_data = self.cog_invoked_stats.get(date_today())
        data = '\n'.join(f"**{key}**: successful = *{value.get('successful')}* | unsuccessful = *{value.get('unsuccessful')}*" for key, value in cogs_data.items() if any(subvalue != 0 for subkey, subvalue in value.items()))

        cogs_item = InvokedCommandsDataItem('cogs', await async_date_today(), data)

        commands_data = self.command_invoked_stats.get(date_today())
        data = '\n'.join(f"**{key}**: successful = *{value.get('successful')}* | unsuccessful = *{value.get('unsuccessful')}*" for key, value in commands_data.items() if value.get('successful') != 0 or value.get('unsuccessful') != 0)
        commands_item = InvokedCommandsDataItem('commands', await async_date_today(), data)

        return overall_item, cogs_item, commands_item

    async def update(self):
        self.command_invoked_stats.save_overall()
        log.debug("'%s' command staff soldier was UPDATED", str(self))

    def retire(self):
        for holder in self.stats_holder:
            holder.save_data()
        self.command_invoked_stats.save_overall()
        log.debug("'%s' command staff soldier was RETIRED", str(self))

    def after_action(self):

        async def record_command_invocation(ctx):
            _command = ctx.command
            _cog = _command.cog
            _command = _command.name
            _cog = str(_cog)
            if _command in ['shutdown', "get_command_stats", None, '']:
                return
            if _cog in [None]:
                return

            self.cog_invoked_stats.add_tick(_cog, ctx.command_failed)
            self.command_invoked_stats.add_tick(_command, ctx.command_failed)
            log.debug("command invocations was recorded")

        return self.bot.after_invoke(record_command_invocation)

    def __str__(self) -> str:
        return self.__class__.__name__


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
