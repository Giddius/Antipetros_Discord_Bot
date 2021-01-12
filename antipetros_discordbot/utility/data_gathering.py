

# region [Imports]

# * Standard Library Imports -->

import asyncio
import gc
import logging
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
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


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
import discord
from discord.ext import commands, tasks

# * PyQt5 Imports -->


# * Gid Imports -->

import gidlogger as glog
from gidtools.gidfiles import (QuickFile, readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
                               dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

PERMISSION_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'permission_data.json')
ROLE_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'role_data.json')
CHANNEL_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'channel_data.json')
GENERAL_DATA_OUTPUT = APPDATA['general_data.json']
MEMBERS_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'members_data.json')
ROLE_CHANNEL_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'role_channel_data.json')
# endregion[Constants]


async def get_member_data(bot):
    member_data = {"by_roles": {}}
    for role in await bot.antistasi_guild.fetch_roles():
        if '@everyone' not in role.name:
            member_data['by_roles'][role.name] = {mem.name: mem.id for mem in role.members}
    writejson(member_data, MEMBERS_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_general_data(bot):
    general_data = {"antistasi_guild_id": 449481990513754112}
    general_data['owner_id'] = bot.antistasi_guild.owner_id
    general_data['filesize_limit'] = bot.antistasi_guild.filesize_limit
    general_data['filesize_limit_mb'] = bot.antistasi_guild.filesize_limit / (1024 * 1024)
    try:
        general_data['webhooks'] = [webhook.name for webhook in await bot.antistasi_guild.webhooks()]
    except Exception as error:
        log.error(error)
    writejson(general_data, GENERAL_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_role_data(bot):
    role_data = {"role_list": {}, "role_info_list": {}}
    try:
        for role in await bot.antistasi_guild.fetch_roles():
            role_data["role_list"][role.name] = role.id
            role_data["role_info_list"][role.name] = {'position': role.position,
                                                      'mentionable': role.mentionable,
                                                      'permissions': {perm[0]: perm[1] for perm in role.permissions},
                                                      'color': role.color.to_rgb(),
                                                      'create_time': role.created_at.isoformat(timespec='seconds'),
                                                      'mention_string': role.mention}

    except Exception as error:
        log.error(error)
    writejson(role_data, ROLE_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_channel_data(bot):
    channel_dict = {'channel_list': {}, 'category_channels': {}, 'Antipetros_permissions': {}}
    channel_dict['category_channels'] = {cat.name: cat.id for cat in bot.antistasi_guild.categories}

    for channel in bot.antistasi_guild.channels:
        channel_dict['channel_list'][channel.name] = channel.id
        channel_dict['Antipetros_permissions'][channel.name] = {perm[0]: perm[1] for perm in channel.permissions_for(bot.bot_member)}
    writejson(channel_dict, CHANNEL_DATA_OUTPUT, indent=4)


async def get_channel_role_data(bot):
    role_dict = {}
    for role in await bot.antistasi_guild.fetch_roles():
        if '@everyone' not in role.name:
            if role.name not in role_dict:
                role_dict[role.name] = {}
            for channel in bot.antistasi_guild.channels:
                try:
                    role_dict[role.name][channel.name] = {perm[0]: perm[1] for perm in channel.permissions_for(role.members[0])}
                except IndexError:
                    log.error(str([member.name for member in role.members]))
    writejson(role_dict, ROLE_CHANNEL_DATA_OUTPUT, sort_keys=False, indent=4)


async def gather_data(bot):
    await get_general_data(bot)
    await get_channel_data(bot)
    await get_role_data(bot)
    await get_member_data(bot)
    await get_channel_role_data(bot)
