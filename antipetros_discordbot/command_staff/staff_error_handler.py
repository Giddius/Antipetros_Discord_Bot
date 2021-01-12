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
import traceback

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

from discord import Embed, File

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

from fuzzywuzzy import fuzz, process as fuzzprocess


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
from antipetros_discordbot.utility.misc import color_hex_embed, async_split_camel_case_string
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.exceptions import MissingAttachmentError
# endregion[Imports]

# region [TODO]

# TODO: rebuild whole error handling system
# TODO: make it so that creating the embed also sends it, with more optional args

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
EMBED_SYMBOLS = loadjson(APPDATA["embed_symbols.json"])
# endregion[Constants]


class ErrorHandler(CommandStaffSoldierBase):

    def __init__(self, bot, command_staff):
        self.bot = bot
        self.command_staff = command_staff
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.error_handle_table = {commands.MaxConcurrencyReached: self._handle_max_concurrency,
                                   commands.CommandOnCooldown: self._handle_command_on_cooldown,
                                   commands.errors.BadArgument: self._handle_bad_argument,
                                   MissingAttachmentError: self._handle_missing_attachment}
        self.default_delete_after_seconds = 120
        glog.class_init_notification(log, self)

    async def handle_errors(self, ctx, error, error_traceback):
        await self.error_handle_table.get(type(error), self._default_handle_error)(ctx, error, error_traceback)

    async def _default_handle_error(self, ctx, error, error_traceback):
        log.error('Ignoring exception in command {}:'.format(ctx.command))
        log.error(str(error), exc_info=True)
        await self.bot.message_creator(embed=await self.error_reply_embed(ctx, error, 'Error With No Special Handling Occured', msg=str(error), error_traceback=error_traceback))

    async def _handle_missing_attachment(self, ctx, error, error_traceback):
        await ctx.channel.send(delete_after=self.default_delete_after_seconds, embed=await self.error_reply_embed(ctx,
                                                                                                                  error,
                                                                                                                  'Missing Attachments',
                                                                                                                  f'{ctx.author.mention}\n{ZERO_WIDTH}\n **{str(error)}**\n{ZERO_WIDTH}'))

    async def _handle_bad_argument(self, ctx, error, error_traceback):
        await ctx.channel.send(delete_after=self.default_delete_after_seconds, embed=await self.error_reply_embed(ctx,
                                                                                                                  error,
                                                                                                                  'Wrong Argument',
                                                                                                                  f'{ctx.author.mention}\n{ZERO_WIDTH}\n **You tried to invoke `{ctx.command.name}` with an wrong argument**\n{ZERO_WIDTH}\n```shell\n{ctx.command.name} {ctx.command.signature}\n```',
                                                                                                                  error_traceback=error_traceback))
        await ctx.message.delete()
        await ctx.send(embed=await self.error_message_embed(ctx, error))
        log.error("Error '%s' was caused by '%s' on the command '%s' with args '%s'", error.__class__.__name__, ctx.author.name, ctx.command.name, ctx.args)

    async def _handle_command_on_cooldown(self, ctx, error, error_traceback):
        await ctx.channel.send(embed=await self.error_reply_embed(ctx, error, 'STOP SPAMMING!', f'{ctx.author.mention}\n{ZERO_WIDTH}\n **Your mother was a hamster and your father smelt of elderberries!**', error_traceback=error_traceback), delete_after=self.default_delete_after_seconds)
        await ctx.message.delete()
        await ctx.send(embed=await self.error_message_embed(ctx, error))
        log.error("Error '%s' was caused by '%s' on the command '%s' with args '%s'", error.__class__.__name__, ctx.author.name, ctx.command.name, ctx.args)

    async def _handle_max_concurrency(self, ctx, error, error_traceback):
        await ctx.channel.send(embed=await self.error_reply_embed(ctx, error, 'STOP SPAMMING!', f'{ctx.author.mention}\n{ZERO_WIDTH}\n **Your mother was a hamster and your father smelt of elderberries!**', error_traceback=error_traceback), delete_after=self.default_delete_after_seconds)
        await ctx.message.delete()

        log.error("Error '%s' was caused by '%s' on the command '%s' with args '%s'", error.__class__.__name__, ctx.author.name, ctx.command.name, ctx.args)

    async def error_reply_embed(self, ctx, error, title, msg, error_traceback=None):
        embed = Embed(title=title, description=f"{ZERO_WIDTH}\n{msg}\n{ZERO_WIDTH}", color=self.command_staff.color('red').int, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning'))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        if error_traceback is not None:
            embed.add_field(name='Traceback', value=str(error_traceback)[0:500])
        if ctx.command is not None:
            embed.set_footer(text=f"Command: `{ctx.command.name}`\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{await async_split_camel_case_string(error.__class__.__name__)}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")
        else:
            embed.set_footer(text=f"text: {ctx.message.content}\n{ZERO_WIDTH}\n By User: `{ctx.author.name}`\n{ZERO_WIDTH}\n Error: `{await async_split_camel_case_string(error.__class__.__name__)}`\n{ZERO_WIDTH}\n{ZERO_WIDTH}")

        return embed

    async def error_message_embed(self, ctx, error, msg=ZERO_WIDTH):
        embed = Embed(title='ERROR', color=self.command_staff.color('orange').int, timestamp=datetime.utcnow(), description=ZERO_WIDTH + '\n' + msg + '\n' + ZERO_WIDTH)
        embed.set_thumbnail(url=EMBED_SYMBOLS.get('warning'))
        try:
            embed.add_field(name=await async_split_camel_case_string(error.__class__.__name__), value=f"error occured with command: {ctx.command.name} and arguments: {str(ctx.args)}")
        except AttributeError:
            embed.add_field(name=await async_split_camel_case_string(error.__class__.__name__), value="command not found\n" + ZERO_WIDTH + '\n', inline=False)
            corrections = fuzzprocess.extract(ctx.message.content.split(' ')[1], [command.name for command in self.bot.commands], scorer=fuzz.token_set_ratio, limit=3)
            if corrections is not None:
                embed.add_field(name='did you mean:', value=ZERO_WIDTH + '\n' + f'\n{ZERO_WIDTH}\n'.join(correction[0] for correction in corrections), inline=False)
            embed.set_footer(text=f'to get a list of all commands use:\n@AntiPetros {self.bot.help_invocation}\n{ZERO_WIDTH}\n{ZERO_WIDTH}')

        return embed

    async def if_ready(self):
        log.debug("'%s' command staff soldier is READY", str(self))

    async def update(self):
        log.debug("'%s' command staff soldier was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' command staff soldier was RETIRED", str(self))


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
