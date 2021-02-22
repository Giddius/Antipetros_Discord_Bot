
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
from typing import Union, TYPE_CHECKING
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import unicodedata
from io import BytesIO
from textwrap import dedent

# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from discord import DiscordException, Embed, File
from async_property import async_property
from dateparser import parse as date_parse
from webdav3.client import Client
from icecream import ic
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, save_commands, CogConfigReadOnly, make_config_name, is_even, owner_or_admin
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2
from antipetros_discordbot.utility.named_tuples import CITY_ITEM, COUNTRY_ITEM
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.the_dragon import THE_DRAGON
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_antistasi_log_watcher_cog import LogFile, LogServer
from antipetros_discordbot.utility.nextcloud import NEXTCLOUD_OPTIONS
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

COG_NAME = "AntistasiLogWatcherCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class AntistasiLogWatcherCog(commands.Cog, command_attrs={'name': COG_NAME, "description": ""}):
    """
    [summary]

    [extended_summary]

    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    already_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,
                             "2021-02-18 11:00:11")}

    required_config_data = dedent("""
                                  log_file_warning_size_threshold = 200mb,
                                  max_amount_get_files = 5
                                    """).strip('\n')
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')

        self.nextcloud_base_folder = "Antistasi_Community_Logs"
        self.server = {}
        self.update_log_file_data_loop_is_first_loop = True
        self.check_oversized_logs_loop_is_first_loop = True

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def already_notified(self):
        if os.path.exists(self.already_notified_savefile) is False:
            writejson([], self.already_notified_savefile)
        return loadjson(self.already_notified_savefile)


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await self.get_base_structure()
        self.update_log_file_data_loop.start()
        self.check_oversized_logs_loop.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=5)
    async def update_log_file_data_loop(self):
        if self.update_log_file_data_loop_is_first_loop is True:
            log.debug('postponing loop "update_log_file_data_loop", as it should not run directly at the beginning')
            self.update_log_file_data_loop_is_first_loop = False
            return

        for folder_name, folder_item in self.server.items():
            log.debug("updating log files for '%s'", folder_name)
            await folder_item.update()
            await asyncio.sleep(5)

    @tasks.loop(minutes=8)
    async def check_oversized_logs_loop(self):
        if self.check_oversized_logs_loop_is_first_loop is True:
            log.debug('postponing loop "check_oversized_logs_loop", as it should not run directly at the beginning')
            self.check_oversized_logs_loop_is_first_loop = False
            return

        for folder_name, folder_item in self.server.items():
            log.debug("checking log files of '%s', for oversize", folder_name)
            oversize_items = await folder_item.get_oversized_items()
            oversize_items = [log_item for log_item in oversize_items if log_item.etag not in self.already_notified]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    @commands.is_owner()
    async def check_newest_files(self, ctx, server: str, sub_folder: str, amount: int = 1):
        max_amount = COGS_CONFIG.retrieve(self.config_name, 'max_amount_get_files', typus=int, direct_fallback=5)
        if amount > max_amount:
            await ctx.send(f'You requested more files than the max allowed amount of {max_amount}, aborting!')
            return
        server = server.casefold()
        folder_item = self.server[server]
        await folder_item.newest_log_file(ctx, sub_folder, amount)


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def get_base_structure(self):
        nextcloud_client = Client(NEXTCLOUD_OPTIONS)
        for folder in await self.bot.execute_in_thread(nextcloud_client.list, self.nextcloud_base_folder):
            folder = folder.strip('/')
            if folder != self.nextcloud_base_folder and '.' not in folder:
                folder_item = LogServer(self.nextcloud_base_folder, folder)
                await folder_item.get_data()
                self.server[folder.casefold()] = folder_item
            await asyncio.sleep(1)
        log.info(str(self) + ' collected server names: ' + ', '.join([key for key in self.server]))


# endregion [HelperMethods]

# region [SpecialMethods]


    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def cog_unload(self):
        self.update_log_file_data_loop.stop()
        self.check_oversized_logs_loop.stop()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(AntistasiLogWatcherCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
