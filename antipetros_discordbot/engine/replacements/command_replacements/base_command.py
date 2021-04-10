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
import icecream as ic
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
from .helper import JsonMetaDataProvider, JsonAliasProvider, SourceCodeProvider
from antipetros_discordbot.utility.misc import highlight_print
from antipetros_discordbot.utility.data import COG_CHECKER_ATTRIBUTE_NAMES
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
    meta_data_provider = JsonMetaDataProvider()
    alias_data_provider = JsonAliasProvider()
    source_code_data_provider = SourceCodeProvider()
    bot_mention_regex = re.compile(r"\@AntiPetros|\@AntiDEVtros", re.IGNORECASE)
    bot_mention_placeholder = '@BOTMENTION'
    gif_folder = APPDATA['gifs']

    def __init__(self, func, **kwargs):
        self.name = func.__name__ if kwargs.get("name") is None else kwargs.get("name")
        self.extra_aliases = kwargs.pop("aliases", None)
        self.get_meta_data = self.meta_data_provider.get_auto_provider(self)
        self.set_meta_data = self.meta_data_provider.set_auto_provider(self)
        self.get_alias = self.alias_data_provider.get_auto_provider(self)
        self.set_alias = self.alias_data_provider.set_auto_provider(self)
        self.remove_alias = self.alias_data_provider.remove_auto_provider(self)
        self.get_source_code = self.source_code_data_provider.get_auto_provider(self)
        super().__init__(func, **kwargs)
        self.module = sys.modules[func.__module__]

    async def get_source_code_image(self):
        return await asyncio.to_thread(self.get_source_code, typus='image')

    @property
    def enabled(self):
        return self.module.get_command_enabled(self.name)

    @enabled.setter
    def enabled(self, value):
        pass

    @property
    def hidden(self):
        return self.get_meta_data('hidden', False)

    @hidden.setter
    def hidden(self, value):
        pass

    @property
    def aliases(self):
        return self.get_alias(extra_aliases=self.extra_aliases)

    @aliases.setter
    def aliases(self, value):
        pass

    @property
    def dynamic_help(self):
        _help = self.get_meta_data('help', None)
        if _help in [None, ""]:
            _help = self.help
        if _help in [None, ""]:
            _help = 'NA'
        return inspect.cleandoc(_help)

    @dynamic_help.setter
    def dynamic_help(self, value):
        self.set_meta_data('help', value)

    @property
    def dynamic_brief(self):
        brief = self.get_meta_data('brief', None)
        if brief in [None, ""]:
            brief = self.brief
        if brief in [None, ""]:
            brief = 'NA'
        return brief

    @dynamic_brief.setter
    def dynamic_brief(self, value):
        self.set_meta_data('brief', value)

    @property
    def dynamic_description(self):
        description = self.get_meta_data('description', None)
        if description in [None, ""]:
            description = self.description
        if description in [None, ""]:
            description = 'NA'
        return inspect.cleandoc(description)

    @dynamic_description.setter
    def dynamic_description(self, value):
        self.set_meta_data('description', value)

    @property
    def dynamic_short_doc(self):
        short_doc = self.get_meta_data('short_doc', None)
        if short_doc in [None, ""]:
            short_doc = self.short_doc
        if short_doc in [None, ""]:
            short_doc = 'NA'
        return short_doc

    @dynamic_short_doc.setter
    def dynamic_short_doc(self, value):
        self.set_meta_data('short_doc', value)

    @property
    def dynamic_usage(self):
        usage = self.get_meta_data('usage', None)
        if usage in [None, ""]:
            usage = self.usage
        if usage in [None, ""]:
            usage = 'NA'
        return usage

    @dynamic_usage.setter
    def dynamic_usage(self, value):
        self.set_meta_data('usage', value)

    @property
    def dynamic_example(self):
        example = self.get_meta_data('example', None)
        if example in [None, ""]:
            example = 'NA'
        if self.cog.bot.bot_member is not None:
            return example.replace(self.bot_mention_placeholder, self.cog.bot.bot_member.mention)
        else:
            return example

    @dynamic_example.setter
    def dynamic_example(self, value):
        self.set_meta_data('example', value)

    @property
    def gif(self):
        for gif_file in os.scandir(self.gif_folder):
            if gif_file.is_file() and gif_file.name.casefold() == f"{self.name}_command.gif".casefold():
                return pathmaker(gif_file.path)
        return None

    @property
    def github_link(self):
        return self.get_source_code('link')

    @property
    def dynamic_allowed_channels(self):
        allowed_channels = []
        for check in self.checks:
            if hasattr(check, "allowed_channels"):
                allowed_channels += check.allowed_channels(self)
        if allowed_channels == []:
            return ['NA']
        return allowed_channels

    @property
    def dynamic_allowed_roles(self):
        allowed_roles = []
        for check in self.checks:
            if hasattr(check, "allowed_roles"):
                allowed_roles += check.allowed_roles(self)
        if allowed_roles == []:
            return ['NA']
        return allowed_roles

    @property
    def dynamic_allowed_in_dms(self):
        values = []
        for check in self.checks:
            if hasattr(check, "allowed_in_dm"):
                values.append(check.allowed_in_dm(self))
        if values == []:
            return True
        return all(values)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
