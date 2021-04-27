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
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, Seperators
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file

from typing import TYPE_CHECKING, Any, Union, Optional, Callable, Iterable, List, Dict, Set, Tuple, Mapping, Coroutine, Awaitable
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

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

# endregion[Constants]


class RulesCog(AntiPetrosBaseCog, command_attrs={"categories": CommandCategory.ADMINTOOLS, "hidden": True}):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

    rules_channel_id = 648725988813045765
    rules_message_regex = re.compile(r"^(?P<number>\d+(\.\d)?)[\)\.]\s?\-?(?P<text>.*)")
    links_message_regex = re.compile(r"(?P<name>.*)\n(?P<link>https\:\/\/.*)")
    fake_fight_club_rules = {'1st RULE': 'You do not talk about **Antistasi**.',
                             '2nd RULE': 'You __DO__ __NOT__ talk about **Antistasi**.',
                             '3rd RULE': 'If someone surrenders or goes limp, double tap him to be sure.',
                             '4th RULE': 'Only twenty guys to a mega-squad.',
                             '5th RULE': 'One mega-squad at a time.',
                             '6th RULE': 'No priest outfit, no shoes, wear sandals.',
                             '7th RULE': 'Campaigns will go on till sunday or till we finally killed all '
                             'civis.',
                             '8th RULE': 'If this is your first night at **Antistasi**, you __HAVE__ to '
                             'squadlead.'}


# endregion [ClassAttributes]

# region [Init]

    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.rules_messages = {}
        self.ready = False
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def rules_channel(self):
        return self.bot.sync_channel_from_id(self.rules_channel_id)

# endregion [Properties]

# region [Setup]
    @universal_log_profiler
    async def on_ready_setup(self):
        asyncio.create_task(self.get_rules_messages())
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name="on_raw_message_edit")
    @universal_log_profiler
    async def update_rules(self, payload: discord.RawMessageUpdateEvent):
        if payload.channel_id != self.rules_channel_id:
            return
        asyncio.create_task(self.get_rules_messages())

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(False)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def exploits_rules(self, ctx: commands.Context):
        embed_data = await self._make_rules_embed(self.rules_messages.get('exploits'))
        msg = await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
        bertha_emoji = self.bot.bertha_emoji
        if bertha_emoji is not None:
            await msg.add_reaction(bertha_emoji)
        if ctx.message.reference is not None:
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(False)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def community_rules(self, ctx: commands.Context):
        embed_data = await self._make_rules_embed(self.rules_messages.get('community'))
        msg = await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
        bertha_emoji = self.bot.bertha_emoji
        if bertha_emoji is not None:
            await msg.add_reaction(bertha_emoji)
        if ctx.message.reference is not None:
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(False)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def server_rules(self, ctx: commands.Context):
        embed_data = await self._make_rules_embed(self.rules_messages.get('server'))
        msg = await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
        bertha_emoji = self.bot.bertha_emoji
        if bertha_emoji is not None:
            await msg.add_reaction(bertha_emoji)
        if ctx.message.reference is not None:
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(False)
    @commands.cooldown(1, 90, commands.BucketType.channel)
    async def all_rules(self, ctx: commands.Context):
        await self.exploits_rules(ctx)
        await self.community_rules(ctx)
        await self.server_rules(ctx)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(False)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def better_rules(self, ctx: commands.Context):
        fields = []
        for rule_num, rule_text in self.fake_fight_club_rules.items():
            fields.append(self.bot.field_item(name=f"**{rule_num}**", value=rule_text))
        embed_data = await self.bot.make_generic_embed(title='The Better Community Rules',
                                                       description="Welcome to ~~  FIGHT  ~~ **ANTISTASI**",
                                                       footer={'text': '\\s ... Big \\S'},
                                                       fields=fields,
                                                       thumbnail='stupid_logo',
                                                       color='pink')

        await ctx.reply(**embed_data)


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    @universal_log_profiler
    async def _make_rules_embed(self, rule_message: discord.Message):
        fields = await self.parse_rules(rule_message)
        fields.append(self.bot.field_item(name="Additional Rules Documents", value='\n'.join(await self.parse_links())))
        timestamp = rule_message.edited_at if rule_message.edited_at is not None else rule_message.created_at
        title = rule_message.content.splitlines()[0] if '----' not in rule_message.content.splitlines()[0].strip('*') else rule_message.content.splitlines()[1]
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=self.rules_channel.mention,
                                                       timestamp=timestamp,
                                                       footer={'text': "Last updated:"},
                                                       fields=fields,
                                                       thumbnail='bertha_emoji_version',
                                                       color='red')
        return embed_data

    @universal_log_profiler
    async def get_rules_messages(self):
        self.rules_messages = {}
        async for message in self.rules_channel.history(limit=None):
            content = message.content.strip().strip('-*').strip()
            first_line = content.splitlines()[0].strip('*_').casefold()
            if first_line == 'community rules':
                self.rules_messages['community'] = message
            elif first_line == 'server rules':
                self.rules_messages['server'] = message
            elif first_line == 'additional rule and guideline documents':
                self.rules_messages['links'] = message
            elif first_line == 'a summary of currently known and reported exploits:':
                self.rules_messages['exploits'] = message

    @universal_log_profiler
    async def parse_rules(self, message: discord.Message) -> list:
        fields = []
        for line in message.content.splitlines():
            line = line.strip('*').strip('_').strip()
            line_match = self.rules_message_regex.search(line)
            if line_match:
                number = line_match.group('number').strip('*')
                text = line_match.group('text').strip('*').strip().strip('*')
                if '.' not in number:
                    number = Seperators.make_line('double', 10) + f'\n\nRule {number}'
                else:
                    number = f'Rule {number}'
                fields.append(self.bot.field_item(name=f"{number}", value=text))
        fields.append(self.bot.field_item(name=Seperators.make_line('double', 10), value=ZERO_WIDTH))
        return fields

    @universal_log_profiler
    async def parse_links(self) -> list:
        links = []
        for item_match in self.links_message_regex.finditer(self.rules_messages.get('links').content):
            name = item_match.group('name').strip()
            link = item_match.group('link').strip()
            links.append(f"🔗 [{name}]({link})")
        return links


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
    bot.add_cog(RulesCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
