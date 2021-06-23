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
from typing import Optional, Union, Any, TYPE_CHECKING, Callable, Iterable, List, Dict, Set, Tuple, Mapping
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


import gidlogger as glog


from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_write_json, async_load_json
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI, letter_to_emoji, CANCEL_EMOJI
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler
from PIL import Image
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import alternative_better_shorten
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

from matplotlib import pyplot as plt

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


class VoteOptionItem:

    def __init__(self, item: Any, emoji: Optional[Union[str, discord.Emoji]] = None):
        self.vote_item = None
        self.item = item
        self.emoji = emoji

    def ensure_emoji(self):
        if self.emoji is None:
            self.emoji = self.vote_item.request_emoji()

    def __str__(self) -> str:
        return str(self.item)

    def __repr__(self) -> str:
        return repr(self.item)


class VoteItem:
    bot = None
    default_emojis = ALPHABET_EMOJIS
    lock = asyncio.Lock()

    def __init__(self,
                 options: Iterable[VoteOptionItem],
                 end_at: datetime,
                 allowed_roles: Iterable[discord.Role] = None,
                 allowed_members: Iterable[discord.Member] = None,
                 after_report: bool = False,
                 emoji_list: Iterable[discord.Emoji] = None):
        self.allowed_emojis: frozenset[Union[str, discord.Emoji]] = None
        self.emoji_list = self.default_emojis.copy() if emoji_list is None else emoji_list
        self.options: dict[VoteOptionItem] = self._handle_options(options)
        self.end_at = end_at
        self.allowed_roles = set(allowed_roles) if allowed_roles is not None else allowed_roles
        self.allowed_members = set(allowed_members) if allowed_members is not None else allowed_members
        self.after_report = after_report

        self.embed_parameter = {"title": "Vote",
                                "description": ZERO_WIDTH,
                                "thumbnail": None}

        self.vote_message: discord.Message = None
        self.diagram_message: discord.Message = None

        self.queue = asyncio.Queue()
        self.add_votes_task: asyncio.Task = None
        self.update_embed_loop_task: asyncio.Task = None
        self.votes = {}
        for emoji, option in self.options.items():
            self.votes[f'start_for_{str(option)}'] = option

    def set_description(self, description: str):
        self.embed_parameter['description'] = description

    def set_title(self, title: str):
        self.embed_parameter['title'] = title

    def set_thumbnail(self, thumbnail: Union[str, bytes, Image.Image]):
        self.embed_parameter['thumbnail'] = thumbnail

    def _handle_options(self, options):
        _out = {}
        for option in options:
            option.vote_item = self
            option.ensure_emoji()
            _out[str(option.emoji)] = option
        self.allowed_emojis = frozenset([str(emoji) for emoji in _out])
        return _out

    def request_emoji(self):
        return self.emoji_list.pop(0)

    async def emoji_to_item(self, emoji):
        return self.options.get(str(emoji))

    async def add_votes(self):
        while True:
            asyncio.create_task(self.update_embed())
            vote_member, emoji = await self.queue.get()
            self.votes[vote_member] = await self.emoji_to_item(emoji)
            asyncio.create_task(self.update_embed())

    async def update_embed_loop(self):
        while True:
            await self.update_embed()
            await asyncio.sleep(0.5)

    async def handle_reaction(self, payload: discord.RawReactionActionEvent):
        await self.vote_message.remove_reaction(payload.emoji, payload.member)

        if all([self.allowed_roles is None or not set(payload.member.roles).isdisjoint(self.allowed_roles),
                self.allowed_members is None or payload.member in self.allowed_members,
                str(payload.emoji) in self.allowed_emojis]):
            log.debug("putting vote")
            await self.queue.put((payload.member, payload.emoji))

    async def after_vote(self):
        await self.vote_message.clear_reactions()
        self.add_votes_task.cancel()
        await self.update_embed(final=True)
        if self.after_report is True:
            diagram = await self.get_diagram_image()
            await self.vote_message.channel.send(file=diagram, allowed_mentions=discord.AllowedMentions.none())

    async def get_diagram_image(self):
        data = []
        for option in self.options.values():
            value = len([item for item in self.votes.values() if item is option])
            data.append((str(option), value))
            await asyncio.sleep(0)
        fig, ax = plt.subplots()
        values = [subdata[1] for subdata in data] if sum([subdata[1] for subdata in data]) != 0 else [1 for subdata in data]
        ax.pie(values, labels=[subdata[0] for subdata in data])
        ax.axis('equal')
        with BytesIO() as bytefile:
            fig.savefig(bytefile, format='png', dpi=150)
            bytefile.seek(0)
            file = discord.File(bytefile, 'vote_data.png')
        return file

    async def embed_data(self):

        fields = []
        for emoji, item in self.options.items():
            fields.append(self.bot.field_item(name=emoji, value=item, inline=False))
        fields.append(self.bot.field_item(name="Temporary Result", value=ZERO_WIDTH, inline=False))
        image = None

        footer = {"text": "Voting ends at, see timestamp"}
        timestamp = self.end_at
        return await self.bot.make_generic_embed(fields=fields, footer=footer, timestamp=timestamp, image=image, **self.embed_parameter)

    async def update_embed(self, final: bool = False):
        embed = self.vote_message.embeds[0]
        embed.remove_field(-1)
        data = []
        for option in self.options.values():
            data.append((str(option), len([item for item in self.votes.values() if item is option]) - 1))
        temp_results = ListMarker.make_list([f"{subdata[0]} -> {subdata[1]}" for subdata in data])
        temp_results = alternative_better_shorten(temp_results, max_length=100, shorten_side="left")
        if final is True:
            embed.add_field(name="Final Result", value=temp_results, inline=False)
            embed.set_footer(text=discord.Embed.Empty, icon_url=discord.Embed.Empty)
        else:
            embed.add_field(name="Temporary Result", value=temp_results, inline=False)
        await self.vote_message.edit(embed=embed)

    async def start_vote(self, channel: discord.TextChannel):

        embed_data = await self.embed_data()
        self.vote_message = await channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        for emoji in self.options:
            await self.vote_message.add_reaction(emoji)

        self.add_votes_task = asyncio.create_task(self.add_votes())


class VotingCog(AntiPetrosBaseCog):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.OUTDATED | CogMetaStatus.CRASHING | CogMetaStatus.EMPTY | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.running_votes = set()
        self.lock = asyncio.Lock()
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        await super().on_ready_setup()
        VoteItem.bot = self.bot
        self.ready = True

    async def update(self, typus: UpdateTypus):
        await super().update(typus)
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name="on_raw_reaction_add")
    async def check_for_vote_listener(self, payload: discord.RawReactionActionEvent):
        if self.ready is False or self.bot.setup_finished is False:
            return
        if payload.member is None:  # This means we are in a DM channel
            return
        if payload.member.bot is True:
            return

        if payload.message_id not in {vote.vote_message.id for vote in self.running_votes}:
            return

        vote = {vote.vote_message.id: vote for vote in self.running_votes}.get(payload.message_id, None)
        if vote is not None:

            await vote.handle_reaction(payload)


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    async def check_vote(self, ctx: commands.Context, minutes: int = 5):
        options = [VoteOptionItem(item="yes", emoji=CHECK_MARK_BUTTON_EMOJI),
                   VoteOptionItem(item="no", emoji=CROSS_MARK_BUTTON_EMOJI),
                   VoteOptionItem(item="wait", emoji=CANCEL_EMOJI)]
        vote = VoteItem(options=options, end_at=datetime.now(tz=timezone.utc) + timedelta(minutes=minutes), after_report=True)
        await vote.start_vote(ctx.channel)
        self.running_votes.add(vote)

        await discord.utils.sleep_until(vote.end_at)
        await vote.after_vote()


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


# endregion [HelperMethods]

# region [SpecialMethods]


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(VotingCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
