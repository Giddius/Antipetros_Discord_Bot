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
import collections.abc
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


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog
from antipetros_discordbot.engine.replacements import CommandCategory

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


class HelpMethodDispatchMap(UserDict):
    def __init__(self, in_dict) -> None:
        super().__init__()
        self.data = in_dict

    def get(self, key, default=None):
        print(f"{type(key)=}")
        if isinstance(key, Enum):
            _out = self.data.get(key, default)
            if _out is not None:
                return _out
        if key in CommandCategory.all_command_categories.values():
            return self.data.get(CommandCategory, default)
        for data_key, value in self.data.items():
            if isinstance(key, data_key):
                return value
        try:
            class_key = key.__class__
            print(class_key)
            _out = self.data.get(class_key, default)
            if _out is not None:
                return _out
        except AttributeError:
            _out = None

        if _out is None:
            raise KeyError(key)

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        if isinstance(key, Enum):
            return key in {data_key for data_key in self.data if isinstance(data_key, Enum)}
        if type(key) in {data_key for data_key in self.data}:
            return True
        try:
            class_key = key.__class__
            if class_key in {data_key for data_key in self.data}:
                return True
        except AttributeError:
            pass
        return False


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
