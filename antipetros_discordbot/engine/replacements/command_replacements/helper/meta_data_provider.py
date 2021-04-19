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
from typing import Union, Callable, Iterable, List, Dict, Optional, Tuple, Any, Callable, Mapping, TYPE_CHECKING
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

# from discord import Embed, File

from discord.ext import commands, tasks, ipc, flags

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, readit, writeit, pathmaker
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class JsonMetaDataProvider:
    gif_folder = APPDATA['gifs']
    data_file = pathmaker(APPDATA['documentation'], 'command_meta_data.json')

    def __init__(self) -> None:
        if os.path.isfile(self.data_file) is False:
            writejson({}, self.data_file)

    @property
    def all_gifs(self):
        _out = {}
        for file in os.scandir(self.gif_folder):
            if file.is_file() and file.name.casefold().endswith('_command.gif'):
                _out[file.name.casefold().removesuffix('_command.gif')] = pathmaker(file.path)
        return _out

    @property
    def meta_data(self) -> dict:
        return loadjson(self.data_file)

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set, command)

    def get(self, command: Union[str, commands.Command], typus: str, fallback=None):
        if isinstance(command, commands.Command):
            command = command.name
        typus = typus.casefold()
        if typus == 'gif':
            return self.all_gifs.get(command.casefold())
        return self.meta_data.get(command.casefold(), {}).get(typus, fallback)

    def set(self, command: Union[str, commands.Command], typus: str, value: Any):
        if isinstance(command, commands.Command):
            command = command.name
        typus = typus.casefold()
        data = self.meta_data
        if command.casefold() not in data:
            data[command.casefold()] = {}
        data[command.casefold()][typus] = value
        self.save(data)

    def save(self, data: dict) -> None:
        writejson(data, self.data_file)

        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
