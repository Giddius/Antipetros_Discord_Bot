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

# import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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


class JsonAliasProvider:
    """
    Dynamically provides all aliases set for a command.
    """
    alias_data_file = pathmaker(APPDATA['documentation'], 'command_aliases.json')
    base_config = ParaStorageKeeper.get_config('base_config')

    def __init__(self):
        if os.path.isfile(self.alias_data_file) is False:
            writejson({}, self.alias_data_file)

    @property
    def default_alias_chars(self) -> List[str]:
        return self.base_config.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')

    @property
    def custom_alias_data(self) -> dict:
        return loadjson(self.alias_data_file)

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set_alias, command)

    def remove_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.remove, command)

    def get(self, command: Union[str, commands.Command], extra_aliases: Union[List, Tuple] = None) -> list[str]:
        if isinstance(command, commands.Command):
            command = command.name
        all_aliases = [] if extra_aliases is None else list(extra_aliases)
        all_aliases = all_aliases + self._get_default_aliases(command) + self._get_custom_aliases(command)
        return list(set(map(lambda x: x.casefold(), all_aliases)))

    def _get_default_aliases(self, command: Union[str, commands.Command]) -> List[str]:
        if isinstance(command, commands.Command):
            command = command.name
        return [command.replace('_', char) for char in self.default_alias_chars if command.replace('_', char) != command]

    def _get_custom_aliases(self, command: Union[str, commands.Command]) -> List[str]:
        if isinstance(command, commands.Command):
            command = command.name
        return self.custom_alias_data.get(command.casefold(), [])

    def set_alias(self, command: commands.Command, new_alias: str):
        new_alias = new_alias.casefold()

        command_name = command.name.casefold()
        data = loadjson(self.alias_data_file)
        if command_name not in data:
            data[command_name] = []
        pre_size = len(data[command_name])
        data[command_name].append(new_alias)
        data[command_name] = list(set(map(lambda x: x.casefold(), data[command_name])))
        post_size = len(data[command_name])
        self.save(data)
        command.cog.bot.refresh_command(command)
        if post_size > pre_size:
            return True
        else:
            return False

    def remove(self, command: Union[str, commands.Command], alias: str):
        alias = alias.casefold()
        if isinstance(command, commands.Command):
            command = command.name
        command = command.casefold()
        data = loadjson(self.alias_data_file)
        if command not in data:
            return False
        if alias not in data[command]:
            return False
        data[command].remove(alias)
        self.save(data)

    def save(self, data: dict) -> None:
        writejson(data, self.alias_data_file)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
