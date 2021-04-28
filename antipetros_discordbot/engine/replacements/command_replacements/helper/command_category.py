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
from abc import ABC, abstractmethod, ABCMeta
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable, TYPE_CHECKING, Optional, List, Set, Tuple, Dict, Mapping, Any, Awaitable
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

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog
from inspect import isabstract, getdoc
from icecream import ic
from marshmallow import Schema, fields
from antipetros_discordbot.schemas import CommandCategorySchema
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.misc import make_config_name
if TYPE_CHECKING:
    from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup
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
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


def subclass_attribute_checker(subclass):
    def is_new_defined(clazz, method):
        """
        https://stackoverflow.com/a/7752095/13989012
        """
        if method not in clazz.__dict__:  # Not defined in clazz : inherited
            return False
        elif hasattr(super(clazz), method):  # Present in parent : overloaded
            return True
        else:  # Not present in parent : newly defined
            return True

    for attr in subclass.needed_attributes:
        if not is_new_defined(subclass, attr):
            raise AttributeError(f"'{subclass}' is missing the necessary new defined attribute '{attr}'!")
    if subclass.docstring == subclass.base_command_category.docstring:
        raise AttributeError(f"'{subclass}' is missing a unique docstring!")


class CommandCategoryMeta(type):
    base_command_category = None
    config_name = None

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)

        if x.__base__ is not object:
            x.is_abstract = False
            x.base_command_category = cls.base_command_category
            subclass_attribute_checker(x)
            x.all_command_categories[x.name.removesuffix('CommandCategory').upper()] = x

        else:
            cls.config_name = make_config_name(x.name)
            cls.base_command_category = x

        return x

    def __repr__(cls) -> str:
        return f"{cls.name}"

    def __str__(cls) -> str:
        return cls.name.removesuffix('CommandCategory')

    def __getattr__(cls, name):
        _out = cls.all_command_categories.get(name, None)
        if _out is None:
            raise AttributeError
        return _out

    def __contains__(cls, item):
        if isinstance(item, commands.Command):
            return item in cls.commands
        raise NotImplementedError

    def __or__(cls, other):
        if cls is other:
            return [cls]
        if issubclass(other, cls.base_command_category):
            return [cls, other]
        raise NotImplementedError

    def __hash__(cls) -> int:
        return hash((cls.name, cls.__class__.__name__))


class CommandCategory(metaclass=CommandCategoryMeta):
    """
    Base Class of all Command Categories.

    Keeps all commands that were added in a subclass in its own 'commands' attribute.

    """
    bot = None
    schema = CommandCategorySchema()
    all_command_categories = {}
    commands = []
    is_abstract = True
    base_command_category = None
    needed_attributes = ['commands', 'allowed_roles']

    always_exclude_role_ids = frozenset({'449481990513754112', '513318914516844559'})  # ["@everyone", "@admin the stupid old one"]

    @classmethod
    @property
    def name(cls):
        return cls.__name__

    @classmethod
    @property
    def docstring(cls):
        return getdoc(cls)

    @classmethod
    def add_command(cls, command: Union["AntiPetrosBaseCommand", "AntiPetrosFlagCommand", "AntiPetrosBaseGroup"]):
        if cls.is_abstract is True:
            raise TypeError(f"'add_to_commands' can't be called on '{cls}' as this class is abstract")
        if command.parent is not None:
            return
        if command not in cls.commands:
            cls.commands.append(command)
        if command not in cls.base_command_category.commands:
            cls.base_command_category.commands.append(command)

        if cls not in command.categories:
            command.categories.append(cls)

    @classmethod
    def dump(cls):
        return cls.schema.dump(cls)

    @classmethod
    @property
    def allowed_roles(cls) -> Set[int]:
        return set()

    @classmethod
    @property
    def extra_roles(cls) -> List[int]:
        return BASE_CONFIG.retrieve(cls.config_name, f"{cls.name.casefold()}_extra_role_ids", typus=List[int], direct_fallback=[])

    @classmethod
    def visibility_check(cls, in_member: discord.Member):
        if cls.is_abstract is True or in_member.bot is True:
            return False
        if in_member.id in cls.bot.owner_ids:
            return True
        if any(role.id in cls.allowed_roles for role in in_member.roles):
            return True
        return False


class GeneralCommandCategory(CommandCategory):
    """
    Category for commands that do not fit any other category.

    """
    commands = []

    @classmethod
    @property
    def allowed_roles(cls) -> Set[str]:
        return {cls.bot.everyone_role_id}


class AdminToolsCommandCategory(CommandCategory):
    """
    Commands that are intended to help admins with their daily tasks.
    """
    commands = []

    @classmethod
    @property
    def allowed_roles(cls) -> Set[str]:
        _out = cls.extra_roles
        for role in cls.bot.antistasi_guild.roles:
            if role.id not in cls.always_exclude_role_ids and not role.name.casefold().endswith("_subscriber"):
                if role.permissions.administrator is True and role.is_bot_managed() is False:
                    _out.append(role.id)
        return set(_out)


class DevToolsCommandCategory(CommandCategory):
    """
    Commands inteded as helpers for the Dev Team
    """
    commands = []
    dev_regex = re.compile(r"(?:\s|^)dev(?:\s|$)", re.IGNORECASE)

    @classmethod
    @property
    def allowed_roles(cls) -> Set[str]:
        _out = cls.extra_roles
        for role in cls.bot.antistasi_guild.roles:
            if role.id not in cls.always_exclude_role_ids and not role.name.casefold().endswith("_subscriber") and role.is_bot_managed() is False:
                if cls.dev_regex.search(role.name):
                    _out.append(role.id)
        return set(_out)


class TeamToolsCommandCategory(CommandCategory):
    """
    A variety of commands, each of which should be helpful to at least one of the Teams
    """
    commands = []
    team_regex = re.compile(r"(?:\s|^)team(?:\s|$)", re.IGNORECASE)

    @classmethod
    @property
    def allowed_roles(cls) -> Set[str]:
        _out = cls.extra_roles
        for role in cls.bot.antistasi_guild.roles:
            if role.id not in cls.always_exclude_role_ids and not role.name.casefold().endswith("_subscriber") and role.is_bot_managed() is False:
                if cls.team_regex.search(role.name):
                    _out.append(role.id)
        return set(_out)


class MetaCommandCategory(CommandCategory):
    """
    Commands that deal with the configuration or maintanance of the Bot itself
    """
    commands = []

    @classmethod
    @property
    def allowed_roles(cls) -> Set[str]:
        _out = cls.extra_roles
        return set(_out)


# class NotImplementedCommandCategory(CommandCategory):
#     """
#     NOT YET IMPLEMENTED!
#     """
#     commands = []

#     @classmethod
#     @property
#     def allowed_roles(cls) -> Set[str]:
#         return set()

#     @classmethod
#     def visibility_check(cls, in_member: discord.Member):
#         return False


# region[Main_Exec]
if __name__ == '__main__':
    pass


# endregion[Main_Exec]
