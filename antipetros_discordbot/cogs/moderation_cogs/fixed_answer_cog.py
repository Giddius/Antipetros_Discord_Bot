# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
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
from enum import Enum, Flag, auto, unique
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
import random
# * Third Party Imports -->
from icecream import ic
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
from async_property import async_property
from dateparser import parse as date_parse

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2, has_attachments, owner_or_admin, log_invoker, only_bob, only_giddi
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState, UpdateTypus
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.utility.id_generation import make_full_cog_id

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

COG_NAME = "FixedAnswerCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class FixedAnswerCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    WiP
    """
# region [ClassAttributes]
    cog_id = 11
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    config_name = CONFIG_NAME
    soon_thumbnails_file = pathmaker(APPDATA["embed_data"], 'soon_thumbnails.json')
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,)}

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
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def soon_thumbnails(self):
        if os.path.isfile(self.soon_thumbnails_file) is False:
            writejson([""], self.soon_thumbnails_file)
        return loadjson(self.soon_thumbnails_file)


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(enabled=get_command_enabled('new_version_eta'), aliases=['eta', "update"])
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    async def new_version_eta(self, ctx: commands.Context):
        title = COGS_CONFIG.retrieve(self.config_name, "eta_message_title", typus=str, direct_fallback='When it is ready')
        description = COGS_CONFIG.retrieve(self.config_name, "eta_message_text", typus=str, direct_fallback=embed_hyperlink("Antistasi Milestones on Github", "https://github.com/official-antistasi-community/A3-Antistasi/milestones"))
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=await self._spread_out_text(description.strip('"')),
                                                       color="light blue",
                                                       thumbnail=random.choice(self.soon_thumbnails),
                                                       author=None,
                                                       timestamp=None)
        await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
        if ctx.message.reference is not None:
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(enabled=get_command_enabled('bob_streaming'), aliases=['bobdev'])
    @only_bob()
    async def bob_streaming(self, ctx: commands.Context, *, extra_msg: str = None):
        announcement_channel_name = COGS_CONFIG.retrieve(self.config_name, 'bob_streaming_announcement_channel_name', typus=str, direct_fallback='announcements')
        announcement_channel = await self.bot.channel_from_name(announcement_channel_name)

        bob_member = await self.bot.retrieve_antistasi_member(346595708180103170)
        extra_message = "Drop in to see what he's up to and to ask any questions you may have" if extra_msg is None else extra_msg

        embed_data = await self.bot.make_generic_embed(title="Bob Murphy is now streaming Antistasi Development!",
                                                       description=extra_message,
                                                       author={"name": bob_member.display_name, "url": "https://www.twitch.tv/bob_murphy", "icon_url": bob_member.avatar_url},
                                                       color=bob_member.color,
                                                       thumbnail="twitch_logo",
                                                       url="https://www.twitch.tv/bob_murphy")
        await announcement_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await announcement_channel.send("https://www.twitch.tv/bob_murphy", allowed_mentions=discord.AllowedMentions.none())

        # await announcement_channel.send(f"**{bob_member.mention} is now streaming Antistasi Development!**\n\n{extra_message}https://www.twitch.tv/bob_murphy", allowed_mentions=discord.AllowedMentions.none())

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    async def _spread_out_text(self, text: str):
        return f"\n{ZERO_WIDTH}\n".join(line for line in text.splitlines() if line != '')


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
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(FixedAnswerCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
