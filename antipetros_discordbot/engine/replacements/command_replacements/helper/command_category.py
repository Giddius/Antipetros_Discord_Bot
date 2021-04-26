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
if TYPE_CHECKING:
    from antipetros_discordbot.engine.replacements import AntiPetrosBaseCommand, AntiPetrosFlagCommand, AntiPetrosBaseGroup
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


def subclass_attribute_checker(subclass):
    for attr in subclass.needed_attributes:
        if not hasattr(subclass, attr):
            raise AttributeError(f"'{subclass}' is missing the necessary attribute '{attr}'!")
    if subclass.docstring == subclass.base_command_category.docstring:
        raise AttributeError(f"'{subclass}' is missing a unique docstring!")


class CommandCategoryMeta(type):
    base_command_category = None

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)

        if x.__base__ is not object:
            x.is_abstract = False
            x.base_command_category = cls.base_command_category
            subclass_attribute_checker(x)
            x.all_command_categories[x.name.removesuffix('CommandCategory').upper()] = x

        else:
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
    schema = CommandCategorySchema()
    all_command_categories = {}
    commands = []
    is_abstract = True
    base_command_category = None
    needed_attributes = ['commands']

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
        cls.commands.append(command)
        cls.base_command_category.commands.append(command)
        command.categories.append(cls)

    @classmethod
    def dump(cls):
        return cls.schema.dump(cls)


class GeneralCommandCategory(CommandCategory):
    """
    Category for commands that do not fit any other category.

    """
    commands = []


class AdminToolsCommandCategory(CommandCategory):
    """
    Commands that are intended to help admins with their daily tasks.
    """
    commands = []


class DevToolsCommandCategory(CommandCategory):
    """
    Commands inteded as helpers for the Dev Team
    """
    commands = []


class TeamToolsCommandCategory(CommandCategory):
    """
    A variety of commands, each of which should be helpful to at least one of the Teams
    """
    commands = []


class MetaCommandCategory(CommandCategory):
    """
    Commands that deal with the configuration or maintanance of the Bot itself
    """
    commands = []


class NotImplementedCommandCategory(CommandCategory):
    """
    NOT YET IMPLEMENTED!
    """
    commands = []
# region[Main_Exec]


if __name__ == '__main__':
    ic(issubclass(GeneralCommandCategory, GeneralCommandCategory.base_command_category))


# endregion[Main_Exec]
