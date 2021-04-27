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
from typing import Union, Callable, Iterable, TYPE_CHECKING, List, Tuple, Set, Dict, Mapping, Any, Awaitable, Optional
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
from .helper import JsonMetaDataProvider, JsonAliasProvider, SourceCodeProvider, JsonCategoryProvider
from antipetros_discordbot.utility.misc import highlight_print
from antipetros_discordbot.utility.data import COG_CHECKER_ATTRIBUTE_NAMES
from antipetros_discordbot.utility.checks import dynamic_enabled_checker
from antipetros_discordbot.schemas import AntiPetrosBaseCommandSchema
from antipetros_discordbot.utility.general_decorator import async_log_profiler
from antipetros_discordbot.engine.replacements.command_replacements.helper.command_category import CommandCategory
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
    bot_mention_placeholder = '@BOTMENTION'

    schema = AntiPetrosBaseCommandSchema()

    def __init__(self, func, **kwargs):
        self.name = func.__name__ if kwargs.get("name") is None else kwargs.get("name")
        self.extra_aliases = kwargs.pop("aliases", None)
        self.data_getters = {'meta_data': self.meta_data_provider.get_auto_provider(self),
                             'alias': self.alias_data_provider.get_auto_provider(self),
                             'source_code': self.source_code_data_provider.get_auto_provider(self)}

        self.data_setters = {'meta_data': self.meta_data_provider.set_auto_provider(self),
                             'alias': self.alias_data_provider.set_auto_provider(self)}

        self.data_removers = {'alias': self.alias_data_provider.remove_auto_provider(self)}
        self._old_data = {'help': None,
                          'brief': None,
                          'description': None,
                          'short_doc': None,
                          'usage': None,
                          'signature': None}
        self.categories = []
        self._handle_category_kwargs(kwargs.get('categories'))
        super().__init__(func, **kwargs)
        self.module_object = sys.modules[func.__module__]

    def _handle_category_kwargs(self, categories: Union[List[CommandCategory], CommandCategory]):
        if categories is not None:
            categories = [categories] if not isinstance(categories, list) else categories
            for category in categories:
                category.add_command(self)

    async def set_alias(self, new_alias: str):
        self.data_setters['alias'](new_alias)

    async def get_source_code_image(self):
        return await asyncio.to_thread(self.data_getters['source_code'], typus='image')

    @property
    def enabled(self):
        return dynamic_enabled_checker(self)

    @enabled.setter
    def enabled(self, value):
        pass

    @property
    def docstring(self):
        return getdoc(self.callback)

    @property
    def aliases(self):
        aliases = self.data_getters['alias'](extra_aliases=self.extra_aliases)
        self.alias = aliases
        return aliases

    @aliases.setter
    def aliases(self, value):
        if isinstance(value, list):
            for alias in value:
                self.data_setters['alias'](alias)
        elif isinstance(value, str):
            self.data_setters['alias'](value)

    @property
    def help(self):
        _help = self.data_getters['meta_data']('help', 'NA')

        return inspect.cleandoc(_help)

    @help.setter
    def help(self, value):
        self._old_data['help'] = value

    @property
    def brief(self):
        brief = self.data_getters['meta_data']('brief', 'NA')
        return brief

    @brief.setter
    def brief(self, value):
        self._old_data['brief'] = value

    @property
    def description(self):
        description = self.data_getters['meta_data']('description', 'NA')
        return inspect.cleandoc(description)

    @description.setter
    def description(self, value):
        self._old_data['description'] = value

    @property
    def short_doc(self):
        short_doc = self.data_getters['meta_data']('short_doc', 'NA')
        return short_doc

    @short_doc.setter
    def short_doc(self, value):
        self._old_data['short_doc'] = value

    @property
    def usage(self):
        usage = self.data_getters['meta_data']('usage', 'NA')

        return usage

    @usage.setter
    def usage(self, value):
        self._old_data['usage'] = value

    @property
    def signature(self):
        signature = self.data_getters['meta_data']('signature', 'NA')
        return signature

    @signature.setter
    def signature(self, value):
        self._old_data["signature"] = value

    @property
    def example(self):
        example = self.data_getters['meta_data']('example', 'NA')

        if self.cog.bot.bot_member is not None:
            return example.replace(self.bot_mention_placeholder, self.cog.bot.bot_member.mention)
        else:
            return example

    @example.setter
    def example(self, value):
        self.data_setters['meta_data']('example', value)

    @property
    def gif(self):
        gif_path = self.data_getters['meta_data']('gif', None)
        return gif_path

    @property
    def github_link(self):
        return self.data_getters['source_code']('link')

    @property
    def allowed_channels(self):
        allowed_channels = ['all']
        for check in self.checks:
            if hasattr(check, "allowed_channels"):
                allowed_channels += check.allowed_channels(self)
        if allowed_channels == []:
            return ['NA']
        if len(allowed_channels) > 1 and 'all' in allowed_channels:
            allowed_channels.remove('all')
        return allowed_channels

    @property
    def allowed_roles(self):
        allowed_roles = []
        for check in self.checks:
            if hasattr(check, "allowed_roles"):
                allowed_roles += check.allowed_roles(self)
        if allowed_roles == []:
            return ['NA']
        if len(allowed_roles) > 1 and 'all' in allowed_roles:
            allowed_roles.remove('all')
        return allowed_roles

    @property
    def allowed_in_dms(self):
        values = []
        for check in self.checks:
            if hasattr(check, "allowed_in_dm"):
                values.append(check.allowed_in_dm(self))
        if values == []:
            return True
        return all(values)

    @property
    def allowed_members(self):
        allowed_members = []
        for check in self.checks:
            if hasattr(check, "allowed_members"):
                allowed_members += check.allowed_members(self)
        if allowed_members == []:
            return ['all']
        if len(allowed_members) > 1 and 'all' in allowed_members:
            allowed_members.remove('all')
        if allowed_members == ['all']:
            return allowed_members
        return list(map(lambda x: x.name, allowed_members))

    def dump(self):
        return self.schema.dump(self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
