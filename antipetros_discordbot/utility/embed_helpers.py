

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

import discord
from discord.ext import commands, tasks


# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.gidtools_functions import pathmaker, loadjson, writejson, readit, readbin, writeit, work_in, writebin
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
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

DEFAULT_FOOTER = "For feature suggestions and feature request, contact @Giddi"

EMBED_SYMBOLS = loadjson(APPDATA["embed_symbols.json"])

# endregion[Constants]


def standard_embed_color():
    color_string = BASE_CONFIG.get('embeds', 'standard_embed_color')
    return int(color_string, base=16)


async def make_basic_embed(title, text=None, footer=None, symbol=None, **kwargs):
    embed_title = str(title).title()
    embed_text = '' if text is None else str(text)

    basic_embed = discord.Embed(title=embed_title, description=embed_text, color=standard_embed_color())
    if symbol is not None:
        basic_embed.set_thumbnail(url=EMBED_SYMBOLS.get(symbol.casefold(), symbol))
    for key, value in kwargs.items():
        field_name = key.replace('_', ' ').title()
        if isinstance(value, tuple):
            field_value = str(value[0])
            field_in_line = value[1]
        else:
            field_value = str(value)
            field_in_line = False
        basic_embed.add_field(name=field_name, value=field_value, inline=field_in_line)
    if footer is not None:
        if isinstance(footer, tuple):
            footer_icon_url = EMBED_SYMBOLS.get(footer[1].casefold(), None)
            basic_embed.set_footer(text=str(footer[0]), icon_url=footer_icon_url)
        else:
            basic_embed.set_footer(text=str(footer))
    else:
        basic_embed.set_footer(text=DEFAULT_FOOTER)
    return basic_embed


async def make_basic_embed_inline(title, text=None, footer=None, symbol=None, **kwargs):
    embed_title = str(title).title()
    embed_text = '' if text is None else str(text)

    basic_embed = discord.Embed(title=embed_title, description=embed_text, color=standard_embed_color())
    if symbol is not None:
        basic_embed.set_thumbnail(url=EMBED_SYMBOLS.get(symbol.casefold(), symbol))
    for key, value in kwargs.items():
        field_name = key.replace('_', ' ').title()

        field_value = str(value)
        field_in_line = True
        basic_embed.add_field(name=field_name, value=field_value, inline=field_in_line)
    if footer is not None:
        if isinstance(footer, tuple):
            footer_icon_url = EMBED_SYMBOLS.get(footer[1].casefold(), None)
            basic_embed.set_footer(text=str(footer[0]), icon_url=footer_icon_url)
        else:
            basic_embed.set_footer(text=str(footer))
    else:
        basic_embed.set_footer(text=DEFAULT_FOOTER)
    return basic_embed


# region[Main_Exec]

if __name__ == '__main__':
    print(standard_embed_color())

# endregion[Main_Exec]
