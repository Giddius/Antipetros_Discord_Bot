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


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

from discord import Embed, File

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import networkx as nx

import matplotlib.pyplot as plt

from graphviz import Digraph

# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog

from antipetros_discordbot.utility.gidtools_functions import (readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
                                                              dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.abstracts.command_staff_abstract import CommandStaffSoldierBase
from antipetros_discordbot.utility.misc import date_today, async_date_today
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class ChannelStatistician(CommandStaffSoldierBase):
    save_folder = APPDATA['stats']
    temp_folder = APPDATA['temp_files']
    exclude_channels = ["website-admin-team", "wiki-mods", "sponsors", "probationary-list", "mute-appeals", "moderator-book", "moderation-team", "event-team", "black-book", "admin-team", "admin-meeting-notes"]
    exclude_categories = ["admin info", "staff rooms", "voice channels"]
    channel_usage_stats_file = pathmaker(APPDATA['stats'], "channel_usage_stats.json")

    def __init__(self, bot, command_staff):
        self.bot = bot
        self.command_staff = command_staff
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.channel_usage_stats = None

        glog.class_init_notification(log, self)

    async def record_channel_usage(self, msg):
        if isinstance(msg.channel, discord.DMChannel):
            return
        if msg.author.id == self.bot.id:
            return
        channel = msg.channel
        if self.is_debug and channel.name == BASE_CONFIG.get('debug', 'current_testing_channel'):
            return
        self.channel_usage_stats['overall'][channel.name] += 1
        self.channel_usage_stats[await async_date_today()][channel.name] += 1
        log.debug('channel usage was logged, for channel "%s"', channel.name)

    async def make_heat_map(self):
        pass

    async def if_ready(self):
        if os.path.isfile(self.channel_usage_stats_file) is False:
            self.channel_usage_stats = {'overall': {}}
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        if self.channel_usage_stats is not None:
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        self.channel_usage_stats = loadjson(self.channel_usage_stats_file)
        for channel in self.bot.antistasi_guild.channels:
            if channel.name not in self.channel_usage_stats['overall']:
                self.channel_usage_stats['overall'][channel.name] = 0
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        await self.update()
        log.debug("'%s' command staff soldier is READY", str(self))

    async def update(self):
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        if await async_date_today() not in self.channel_usage_stats:
            self.channel_usage_stats[await async_date_today()] = {}
        for channel in self.bot.antistasi_guild.channels:
            if channel.name not in self.channel_usage_stats[await async_date_today()]:
                self.channel_usage_stats[await async_date_today()][channel.name] = 0
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)

        log.debug("'%s' command staff soldier was UPDATED", str(self))

    def retire(self):
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        log.debug("'%s' command staff soldier was RETIRED", str(self))


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
