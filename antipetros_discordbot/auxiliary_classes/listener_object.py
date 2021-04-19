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
from typing import Union, Callable, Iterable, Set, Dict, Mapping, List, Tuple, Generator, Awaitable, Any, TYPE_CHECKING
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines, signature, getcomments, getfile, getmodule, getmro, isclass, iscode, iscoroutine
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

from discord.ext import commands, tasks, flags, ipc

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog
from antipetros_discordbot.utility.event_data import ListenerEvents
from antipetros_discordbot.utility.misc import sync_antipetros_repo_rel_path, get_github_line_link
from antipetros_discordbot.schemas.extra_schemas.listener_schema import ListenerSchema
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


class ListenerObject:
    github_base_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/blob/development/"

    def __init__(self, event: Union[str, ListenerEvents], method: Callable, cog: commands.Cog = None):
        self.event = ListenerEvents(event) if isinstance(event, str) else event
        self.method = method
        self.name = self.method.__name__
        self._cog = cog

    @property
    def description(self):
        return getdoc(self.method)

    @property
    def code(self) -> str:
        return getsource(self.method)

    @property
    def file(self):
        return getsourcefile(self.cog.__class__)

    @property
    def source_lines(self):
        return getsourcelines(self.method)

    @property
    def github_link(self):
        return get_github_line_link(self.github_base_url, self.file, self.source_lines)

    @property
    def cog(self) -> commands.Cog:
        if self._cog is not None:
            return self._cog
        # module = getmodule(self.method)
        # for name, class_object in getmembers(module, isclass):
        #     if class_object.__module__ == module.__name__ and isinstance(class_object, commands.Cog):
        #         self._cog = clas
        #         return class_object


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
