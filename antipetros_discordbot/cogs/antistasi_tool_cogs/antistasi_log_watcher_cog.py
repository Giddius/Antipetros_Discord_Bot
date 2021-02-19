
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
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_antistasi_log_watcher_cog import LogFile
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
    allready_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,
                             "2021-02-18 11:00:11")}

    required_config_data = dedent("""
                                    """).strip('\n')
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.nextcloud_client = Client(self.nextcloud_options)
        self.nextcloud_base_folder = "Antistasi_Community_Logs"
        self.server_folder = {}
        self.log_files = []

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def nextcloud_options(self):
        _options = {}
        if os.getenv('NEXTCLOUD_USERNAME') is not None:
            _options['webdav_hostname'] = f"https://antistasi.de/dev_drive/remote.php/dav/files/{os.getenv('NEXTCLOUD_USERNAME')}/"
            _options['webdav_login'] = os.getenv('NEXTCLOUD_USERNAME')
        else:
            raise RuntimeError('no nextcloud Username set')
        if os.getenv('NEXTCLOUD_PASSWORD') is not None:
            _options['webdav_password'] = os.getenv('NEXTCLOUD_PASSWORD')
        else:
            raise RuntimeError('no nextcloud Password set')
        return _options

    @property
    def already_notified(self):
        return loadjson(self.allready_notified_savefile)


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        if os.path.isfile(self.allready_notified_savefile) is False:
            writejson({}, self.allready_notified_savefile)
        writejson(await self.get_base_structure(), self.allready_notified_savefile)
        await self.get_files_info('Mainserver_1', 'Server')
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @commands.is_owner()
    async def list_dev_members(self, ctx):
        msg = ""
        for role_name, members in self.bot.dev_member_by_role.items():
            msg += "\n---\n***__" + role_name.title() + '__***\n'
            msg += '\n'.join(member.name for member in members)
        await ctx.send(msg)

    @auto_meta_info_command()
    @commands.is_owner()
    async def check_file(self, ctx, name: str):
        file = None
        for file_item in self.log_files:
            if file_item.name.casefold() == name.casefold():
                file = file_item
                break
        await self.bot.split_to_messages(ctx, message=await file.content(), syntax_highlighting='python', in_codeblock=True)


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def get_base_structure(self):
        base_structure = loadjson(self.allready_notified_savefile)
        for folder in await self.bot.execute_in_thread(self.nextcloud_client.list, self.nextcloud_base_folder):
            folder = folder.strip('/')
            if not folder.endswith('.md') and folder != self.nextcloud_base_folder:
                if folder not in base_structure:
                    base_structure[folder] = {}
                if folder not in self.server_folder:
                    self.server_folder[folder] = []
                for subfolder in await self.bot.execute_in_thread(self.nextcloud_client.list, f"{self.nextcloud_base_folder}/{folder}"):
                    subfolder = subfolder.strip('/')
                    if subfolder != folder:
                        if subfolder not in base_structure[folder]:
                            base_structure[folder][subfolder] = []
                        if subfolder not in self.server_folder[folder]:
                            self.server_folder[folder].append(subfolder)
        return base_structure

    async def get_files_info(self, server: str, folder: str):
        for file_item in await self.bot.execute_in_thread(partial(self.nextcloud_client.list, f"{self.nextcloud_base_folder}/{server}/{folder}", get_info=True)):
            try:
                instance = LogFile(**file_item, client=self.nextcloud_client)
                if instance not in self.log_files:
                    self.log_files.append(instance)
            except TypeError as error:
                log.error(f"{error} with file {file_item.get('path')}")
        writejson([item.name for item in self.log_files], 'log_file_items.json')
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

        pass

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
