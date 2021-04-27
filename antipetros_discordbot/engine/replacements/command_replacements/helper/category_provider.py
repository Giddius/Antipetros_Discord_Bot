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
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, reduce
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from operator import or_

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
from .command_category import CommandCategory
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


class JsonCategoryProvider:
    """
    Dynamically provides all aliases set for a command.
    """
    category_data_file = pathmaker(APPDATA['documentation'], 'command_categories.json')
    default_category = 'general'

    def __init__(self):
        if os.path.isfile(self.category_data_file) is False:
            writejson({}, self.category_data_file)

    @property
    def category_data(self) -> dict:
        return loadjson(self.category_data_file)

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set_category, command)

    def remove_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.remove, command)

    def get(self, command: Union[str, commands.Command]) -> CommandCategory:
        if isinstance(command, commands.Command):
            command = command.name
        return CommandCategory.deserialize(self.category_data.get(command, 'general'))

    def set_category(self, command: commands.Command, new_category: Union[CommandCategory, str, List[str], List[CommandCategory]]):
        command_name = command.name
        data = self.category_data
        if command_name not in data:
            data[command_name] = []
        if isinstance(new_category, str):
            new_category = CommandCategory.deserialize(new_category)
        elif isinstance(new_category, list):
            if all(isinstance(new_category_item, str) for new_category_item in new_category):
                new_category = CommandCategory.deserialize(new_category)
            elif all(isinstance(new_category_item, CommandCategory) for new_category_item in new_category):
                new_category = reduce(or_, [item for item in new_category])
        data[command_name] += new_category.serialize()
        data[command_name] = list(set(data[command_name]))
        self.save(data)

    def remove(self, command: Union[str, commands.Command], category: Union[str, CommandCategory]):
        raise NotImplementedError()

    def save(self, data: dict) -> None:
        writejson(data, self.category_data_file)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
