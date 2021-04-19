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
from abc import ABC, abstractmethod, ABCMeta, ABC
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable, List, Dict, Optional, Tuple, Any, Union, Callable, Iterable, Set, Sequence, Type, TypeVar, Iterator, NamedTuple, Mapping, Generator, Generic, IO
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
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

# from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog


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


class BaseReactionInstruction(ABC):
    bot = None

    def __init__(self, name: str, emojis: List):
        self.name = name
        self.emojis = emojis

    async def __call__(self, msg: discord.Message):
        if await self.check_trigger(msg) is True:
            for emoji in self.emojis:
                await msg.add_reaction(emoji)

    @abstractmethod
    async def check_trigger(self, message: discord.Message):
        ...

    @classmethod
    @abstractmethod
    async def from_dict(cls, **kwargs):
        ...

    @abstractmethod
    async def to_dict(self):
        ...

    @abstractmethod
    async def get_info_embed(self):
        ...

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.emojis})"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
