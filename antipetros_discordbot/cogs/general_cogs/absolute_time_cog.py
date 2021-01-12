
# region [Imports]

# * Standard Library Imports -->
import gc
import os
import re
import sys
import json
import lzma
import time
import queue
import logging
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union
from datetime import tzinfo, datetime, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
import unicodedata
from io import BytesIO

# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess
import aiohttp
import discord
from discord.ext import tasks, commands
from discord import DiscordException

from async_property import async_property
from pytz import country_timezones, timezone, all_timezones
# * Gid Imports -->
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, readbin, linereadit, writeit, writebin, appendwriteit, loadjson, writejson, pickleit, get_pickled, clearit
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.misc import save_commands, STANDARD_DATETIME_FORMAT
from antipetros_discordbot.utility.checks import in_allowed_channels
from antipetros_discordbot.utility.named_tuples import COUNTRY_ITEM, CITY_ITEM
from antipetros_discordbot.cogs import get_aliases
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
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AbsoluteTimeCog(commands.Cog, command_attrs={'hidden': True, "name": "AbsoluteTimeCog"}):

    # region [ClassAttributes]
    config_name = "absolute_time"
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.registered_timezones_file = APPDATA['registered_timezones.json']
        self._item_id = 0
        self.country_items = self.all_country_as_items()
        self.city_items = self.all_cities_as_item()
        if self.bot.is_debug:
            save_commands(self)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def allowed_channels(self):
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

    @property
    def registered_timezones(self):
        _out = []
        for _id in loadjson(self.registered_timezones_file):
            _out.append(self.id_to_item(_id, self.country_items + self.city_items))
        return _out

    @property
    def all_timezones(self):
        return loadjson(APPDATA['all_timezones.json'])

    @property
    def utc_now(self):
        return datetime.utcnow()

# endregion [Properties]

# region [Setup]

    def all_country_as_items(self):
        _out = []

        for item in loadjson(APPDATA['country_codes.json']):
            _id = self._item_id
            _name = item.get('name')
            _code = item.get('code')
            _country = country_timezones.get(_code)
            _tz = timezone(_country[0])
            _out.append(COUNTRY_ITEM(_id, _name, _code, _tz))
            self._item_id += 1
        return _out

    def all_cities_as_item(self):
        _out = []

        for continent_city_str in self.all_timezones:
            if '/' not in continent_city_str:
                continent = 'general'
                city = continent_city_str
            else:
                continent = continent_city_str.split('/')[0]
                city = continent_city_str.split('/')[-1]
            _out.append(CITY_ITEM(self._item_id, continent, city, timezone(continent_city_str)))
            self._item_id += 1
        return _out


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @commands.command(aliases=get_aliases("to_absolute_times"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("absolute_time", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("absolute_time", 'allowed_channels')))
    async def to_absolute_times(self, ctx):

        pass

    @commands.command(aliases=get_aliases("register_timezone_city"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("absolute_time", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("absolute_time", 'allowed_channels')))
    async def register_timezone_city(self, ctx, in_data):

        registered_items = self.registered_timezones

        item = await self.get_city_or_country(in_data)
        if item is None:
            return
        registered_items.append(item)
        writejson([reg_item.id for reg_item in registered_items], self.registered_timezones_file)
        await ctx.send(f'added timezone {str(item.timezone)} to the registered timezones')

    @commands.command(aliases=get_aliases("tell_all_registered_timezones"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("absolute_time", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("absolute_time", 'allowed_channels')))
    async def tell_all_registered_timezones(self, ctx):

        _out = [item.name + ' ' + str(item.id) + ' ' + str(item.timezone) + ' ----> ' + datetime.now(tz=item.timezone).strftime(STANDARD_DATETIME_FORMAT) for item in self.registered_timezones]
        await self.bot.split_to_messages(ctx, '\n'.join(_out))

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]

    @staticmethod
    def id_to_item(in_id, in_items):
        for item in in_items:
            if int(in_id) == item.id:
                return item

    @staticmethod
    def name_from_item(in_item):
        if isinstance(in_item, str):
            return in_item
        else:
            return in_item.name

    async def get_city_or_country(self, in_data: str):
        country_item, country_score = fuzzprocess.extractOne(in_data, self.country_items, scorer=fuzz.token_sort_ratio, processor=self.name_from_item)
        city_item, city_score = fuzzprocess.extractOne(in_data, self.city_items, scorer=fuzz.token_sort_ratio, processor=self.name_from_item)
        if country_score > city_score:
            return country_item
        elif city_score > country_score:
            return city_item
        else:
            return None

# endregion [HelperMethods]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):

        pass


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AbsoluteTimeCog(bot))
