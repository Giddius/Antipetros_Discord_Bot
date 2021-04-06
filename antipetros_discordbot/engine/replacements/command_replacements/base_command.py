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
import inspect

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks, flags, ipc

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from .helper.alias_provider import AliasProvider
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


class AntiPetrosBaseCommand(commands.Command):
    meta_data_file = pathmaker(APPDATA['documentation'], 'command_help_data.json')
    bot_mention_regex = re.compile(r"\@AntiPetros|\@AntiDEVtros", re.IGNORECASE)
    gif_folder = APPDATA['gifs']

    def __init__(self, func, **kwargs):
        self.name = func.__name__ if kwargs.get("name") is None else kwargs.get("name")
        self.alias_provider = AliasProvider(self.name, kwargs.get("aliases"))
        super().__init__(func, **kwargs)

    @property
    def full_id(self):
        return self._get_full_id()

    @property
    def aliases(self):
        return self.alias_provider.aliases

    @aliases.setter
    def aliases(self, value):
        pass

    @property
    def meta_data(self):
        if os.path.isfile(self.meta_data_file) is False:
            return {}
        return loadjson(self.meta_data_file).get(self.name, {})

    @property
    def help(self):
        return inspect.cleandoc(self.meta_data.get('help', inspect.getdoc(self.callback)))

    @help.setter
    def help(self, value):
        pass

    @property
    def brief(self):
        return self.meta_data.get('brief', None)

    @brief.setter
    def brief(self, value):
        pass

    @property
    def description(self):
        return inspect.cleandoc(self.meta_data.get('description', ''))

    @description.setter
    def description(self, value):
        pass

    @property
    def short_doc(self):
        short_doc = self.meta_data.get('short_doc', None)
        if short_doc is not None:
            return short_doc
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help
        return ''

    @short_doc.setter
    def short_doc(self, value):
        pass

    @property
    def usage(self):
        return self.meta_data.get('usage', None)

    @usage.setter
    def usage(self, value):
        pass

    @property
    def example(self):
        example = self.meta_data.get('example', None)
        return example

    @example.setter
    def example(self, value):
        meta_data = self.get_full_metadata()
        meta_data[self.name]['example'] = value

    @property
    def gif(self):
        for gif_file in os.scandir(self.gif_folder):
            if gif_file.is_file() and gif_file.name.casefold() == f"{self.name}_command.gif".casefold():
                return pathmaker(gif_file.path)
        return None

    def get_full_metadata(self):
        if os.path.exists(self.meta_data_file) is False:
            return {self.name: {}}
        return loadjson(self.meta_data_file)

    def save_full_metadata(self, data):
        writejson(data, self.meta_data_file)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
