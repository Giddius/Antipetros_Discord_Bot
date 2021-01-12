

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
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union, Optional
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from statistics import mean, median, stdev, mode, variance, pvariance
import random
from io import BytesIO
from copy import deepcopy, copy
# * Third Party Imports -->

from discord.ext import commands, tasks, flags
from discord import DiscordException
import discord
from fuzzywuzzy import process as fuzzprocess
import matplotlib.pyplot as plt
from psutil import virtual_memory
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter


# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.misc import seconds_to_pretty
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, bytes2human
from antipetros_discordbot.utility.embed_helpers import make_basic_embed, make_basic_embed_inline
from antipetros_discordbot.utility.misc import save_commands, seconds_to_pretty, async_seconds_to_pretty_normal
from antipetros_discordbot.utility.checks import in_allowed_channels, log_invoker
from antipetros_discordbot.utility.named_tuples import MemoryUsageMeasurement, LatencyMeasurement
from antipetros_discordbot.utility.enums import DataSize
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.converters import DateTimeFullConverter, DateOnlyConverter
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


# endregion[Constants]


class PurgeMessagesCog(commands.Cog, command_attrs={'hidden': True, "name": "PurgeMessagesCog"}):
    config_name = 'purge'

    def __init__(self, bot):
        self.bot = bot
        if self.bot.is_debug:
            save_commands(self)
        glog.class_init_notification(log, self)

    @commands.command(aliases=get_aliases("purge_antipetros"))
    @commands.is_owner()
    @in_allowed_channels(set(COGS_CONFIG.getlist("purge", 'allowed_channels')))
    async def purge_antipetros(self, ctx, and_giddi: Optional[str] = None, number_of_messages: Optional[int] = 1000):

        def is_antipetros(message):
            if and_giddi != "and_giddi":
                return message.author.id == self.bot.id
            return message.author.id in [self.bot.id, self.bot.creator.id]

        await ctx.channel.purge(limit=number_of_messages, check=is_antipetros, bulk=True)
        await ctx.send('done')

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    @commands.command(aliases=get_aliases("purge_msg_from_user"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("general_debug", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("purge", 'allowed_channels')))
    async def purge_msg_from_user(self, ctx, user: discord.User, number_of_messages: Optional[int] = 1000, since: Optional[DateOnlyConverter] = None):

        def is_user(message):
            return message.author.id == user.id

        messages_deleted = await ctx.channel.purge(limit=number_of_messages, check=is_user, after=since, bulk=True)
        await ctx.send(f"deleted {len(messages_deleted)} messages from {user.name}")

# region[Main_Exec]


def setup(bot):
    bot.add_cog(PurgeMessagesCog(bot))

# endregion[Main_Exec]
