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

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog

from antipetros_discordbot.utility.gidtools_functions import (readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
                                                              dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.abstracts.command_staff_abstract import CommandStaffSoldierBase
from antipetros_discordbot.utility.named_tuples import RegexItem
from antipetros_discordbot.utility.exceptions import DuplicateNameError

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


class RegexKeeper(CommandStaffSoldierBase):
    regex_file = APPDATA['regexes_stored.txt']

    def __init__(self, bot, command_staff):
        self.bot = bot
        self.command_staff = command_staff
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.raw_regex_data = ''
        self.regexes = {}
        glog.class_init_notification(log, self)

    def _load_regexes(self):
        self.raw_regex_data = readit(self.regex_file)

    def _process_raw_regexes(self):
        self._load_regexes()
        self.regexes = {}
        for line in self.raw_regex_data.splitlines():
            name, _regex = line.split('=', maxsplit=1)
            name = name.strip()
            _regex = _regex.strip()
            if name not in self.regexes:
                self.regexes[name] = RegexItem(name, _regex)
            else:
                raise DuplicateNameError(name, str(self))

    def _compile_all_regexes(self):
        self._process_raw_regexes()
        for key, value in self.regexes.items():
            self.regexes[key] = value._replace(compiled=re.compile(value.raw))

    def regex(self, regex_name):
        return self.regexes.get(regex_name)

    async def if_ready(self):
        await self.bot.execute_in_thread(self._compile_all_regexes)
        log.debug("'%s' command staff soldier is READY", str(self))

    async def update(self):
        log.debug("'%s' command staff soldier was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' command staff soldier was RETIRED", str(self))


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
