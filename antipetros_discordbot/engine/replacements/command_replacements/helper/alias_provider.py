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

# from discord.ext import commands, tasks

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


class AliasProvider:
    """
    Dynamically provides all aliases set for a command.
    """
    alias_data_file = pathmaker(APPDATA['documentation'], 'command_aliases.json')
    base_config = ParaStorageKeeper.get_config('base_config')

    def __init__(self, command_name: str, extra_aliases: Union[List, Tuple] = None):
        self.command_name = command_name
        self.extra_aliases = [] if extra_aliases is None else extra_aliases

    @property
    def default_alias_chars(self) -> List[str]:
        return self.base_config.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')

    @property
    def custom_alias_data(self) -> dict:
        if os.path.isfile(self.alias_data_file) is False:
            return {}
        return loadjson(self.alias_data_file)

    @property
    def default_aliases(self) -> List[str]:
        default_aliases = []
        for char in self.default_alias_chars:
            mod_name = self.command_name.replace('_', char)
            if mod_name not in default_aliases and mod_name != self.command_name:
                default_aliases.append(mod_name)
        return default_aliases

    @property
    def custom_aliases(self) -> List[str]:
        return self.custom_alias_data.get(self.command_name, [])

    @property
    def aliases(self) -> List[str]:
        aliases = self.default_aliases + self.custom_aliases + self.extra_aliases
        return list(set(map(lambda x: x.casefold(), aliases)))


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
