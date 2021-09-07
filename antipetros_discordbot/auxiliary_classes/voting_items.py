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
from typing import Union, Callable, Iterable, TYPE_CHECKING, Optional, Generator, Any
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
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.abstracts import AbstractConnectSignal
from antipetros_discordbot.utility.emoji_handling import ALPHABET_EMOJIS, NUMERIC_EMOJIS

import discord

import gidlogger as glog
from antipetros_discordbot.utility.discord_markdown_helper import shorten_string, CodeBlock, ListMarker, Seperators, ZERO_WIDTH, embed_hyperlink
from matplotlib import pyplot as plt
from PIL import Image
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class VoteStartedSignal(AbstractConnectSignal):

    async def emit(self, vote: "VoteItem"):
        return await super().emit(vote)


class VoteOptionItem:
    text_regex = re.compile(r"(?P<item>((\w+\s*)|(\d+|\s*))+)\s*\[?(?P<emoji>[^\[\]\s]+)?\s*\]?")

    def __init__(self, item: Any, emoji: Optional[Union[str, discord.Emoji]] = None):
        self.vote_item = None
        self.item = item
        self.emoji = emoji

    def ensure_emoji(self):
        if self.emoji is None:
            self.emoji = self.vote_item.request_emoji()

    @classmethod
    def from_text(cls, text: str) -> "VoteOptionItem":
        if '==' in text:
            item, emoji = map(lambda x: x.strip(), text.split('=='))
            if emoji == "":
                emoji = None
        else:
            item = text.strip()
            emoji = None
        return cls(item=item, emoji=emoji)

    def __str__(self) -> str:
        return str(self.item)

    def __repr__(self) -> str:
        return repr(self.item)


class VoteItem:
    vote_started_signal = VoteStartedSignal()
    bot = None
    default_emojis = ALPHABET_EMOJIS
    lock = asyncio.Lock()

    def __init__(self,
                 name: str,
                 options: Iterable[VoteOptionItem],
                 end_at: datetime,
                 allowed_roles: Iterable[discord.Role] = None,
                 allowed_members: Iterable[discord.Member] = None,
                 after_report: bool = False,
                 report_each_vote: bool = False,
                 show_each_vote: bool = False,
                 emoji_list: Iterable[discord.Emoji] = None):
        self.name = name
        self.allowed_emojis: frozenset[Union[str, discord.Emoji]] = None
        self.emoji_list = self.default_emojis.copy() if emoji_list is None else emoji_list
        self.options: dict[VoteOptionItem] = self._handle_options(options)
        self.end_at = end_at
        self.allowed_roles = set(allowed_roles) if allowed_roles is not None else allowed_roles
        self.allowed_members = set(allowed_members) if allowed_members is not None else allowed_members
        self.after_report = after_report
        self.report_each_vote = report_each_vote
        self.show_each_vote = show_each_vote

        self.embed_parameter = {"description": ZERO_WIDTH,
                                "thumbnail": None}

        self.vote_message: discord.Message = None
        self.diagram_message: discord.Message = None

        self.queue = asyncio.Queue()
        self.add_votes_task: asyncio.Task = None
        self.update_embed_loop_task: asyncio.Task = None
        self.end_vote_task = None
        self.votes = {}
        self.old_votes_data = {}
        self.finished = False

    @property
    def current_result(self):
        _out = Counter(self.votes.values())
        for option in self.options.values():
            if option not in _out:
                _out[option] = 0
        return _out

    def set_description(self, description: str):
        self.embed_parameter['description'] = description

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

            vote_member, emoji = await self.queue.get()
            self.votes[vote_member] = await self.emoji_to_item(emoji)
            await self.update_embed()

    async def update_embed_loop(self):
        while True:
            if self.old_votes_data != self.votes:
                await self.update_embed()
            await asyncio.sleep(0.25)

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
        self.update_embed_loop_task.cancel()
        await self.update_embed(final=True)
        if self.after_report is True:
            await self._send_after_report()
        self.finished = True

    async def _send_after_report(self):
        title = f"Vote Result for {self.name}"
        image = await self.get_diagram_image()
        fields = []
        if self.report_each_vote is False:
            for option, amount in self.current_result.most_common():
                fields.append(self.bot.field_item(name=str(option), value=f"Sum: {amount}", inline=False))
        else:
            for option, amount in self.current_result.most_common():
                voters = ', '.join([member.mention for member, vote_option in self.votes.items() if vote_option is option])
                fields.append(self.bot.field_item(name=str(option), value=f"Sum: {amount}\n{voters}\n{ZERO_WIDTH}", inline=False))
        embed_data = await self.bot.make_generic_embed(title=title, image=image, fields=fields, thumbnail=None)

        await self.vote_message.channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def get_diagram_image(self):
        data = []
        for option, amount in self.current_result.most_common():
            if amount != 0:
                data.append((str(option), amount))
                await asyncio.sleep(0)
        fig, ax = plt.subplots()
        values = [subdata[1] for subdata in data]
        ax.pie(values, labels=[subdata[0] for subdata in data])
        ax.axis('equal')
        with BytesIO() as bytefile:
            fig.savefig(bytefile, format='png', dpi=150)
            bytefile.seek(0)
            file = discord.File(bytefile, 'vote_data.png')
        return file

    async def embed_data(self):

        fields = [self.bot.field_item(name=ZERO_WIDTH, value=Seperators.make_line())]
        for emoji, item in self.options.items():
            fields.append(self.bot.field_item(name=f"{emoji} ⊸ {item}", value=ZERO_WIDTH, inline=False))
        fields.append(self.bot.field_item(name="Temporary Result", value=ZERO_WIDTH, inline=False))
        image = None

        footer = {"text": "Voting ends at, see timestamp", "icon_url": "https://icons.iconarchive.com/icons/martz90/circle/256/clock-icon.png"}
        timestamp = self.end_at
        return await self.bot.make_generic_embed(title=self.name, fields=fields, footer=footer, timestamp=timestamp, image=image, **self.embed_parameter)

    async def update_embed(self, final: bool = False):
        self.old_votes_data = self.votes.copy()
        embed = self.vote_message.embeds[0]
        embed.remove_field(-1)
        embed.timestamp = self.end_at

        temp_results = ListMarker.make_numbered_list([f"__**{option}**__: *{amount}*" for option, amount in self.current_result.most_common()])
        temp_results = shorten_string(temp_results, max_length=1000, shorten_side="left")
        if self.show_each_vote is True:
            temp_results = ListMarker.make_numbered_list(
                [f"__**{option}**__: *{amount}*\n{ZERO_WIDTH}\n{', '.join(member.mention for member,member_vote in self.votes.items() if member_vote is option)}\n{ZERO_WIDTH}" for option, amount in self.current_result.most_common()])
            temp_results = shorten_string(temp_results, max_length=1000, shorten_side="left")
        if final is True:
            embed.add_field(name="Final Result", value=temp_results, inline=False)
            embed.set_footer(text=discord.Embed.Empty, icon_url=discord.Embed.Empty)
        else:
            embed.add_field(name="Temporary Result", value=await asyncio.sleep(0, temp_results), inline=False)
        await self.vote_message.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    async def finish_vote(self):
        self.end_vote_task.cancel()
        await self.after_vote()

    async def cancel_vote(self):
        self.end_vote_task.cancel()
        await self.vote_message.clear_reactions()
        self.add_votes_task.cancel()
        self.update_embed_loop_task.cancel()

        embed = self.vote_message.embeds[0]
        embed.title = f"__***CANCELED***__\n~~{embed.title}~~"
        embed.description = f"__***CANCELED***__\n~~{embed.description}~~"
        embed.timestamp = discord.Embed.Empty
        embed.set_footer(text="CANCELED")
        embed.clear_fields()
        await self.vote_message.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        self.finished = True

    async def end_vote(self):
        now = datetime.now(tz=timezone.utc)
        end_at = self.end_at
        while now <= self.end_at:
            await asyncio.sleep(10)
            now = datetime.now(tz=timezone.utc)
            end_at = self.end_at
        await self.after_vote()

    async def start_vote(self, channel: discord.TextChannel):

        embed_data = await self.embed_data()
        self.vote_message = await channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        for emoji in self.options:
            await self.vote_message.add_reaction(emoji)

        self.add_votes_task = asyncio.create_task(self.add_votes())
        self.update_embed_loop_task = asyncio.create_task(self.update_embed_loop())
        self.end_vote_task = asyncio.create_task(self.end_vote())
        asyncio.create_task(self.vote_started_signal.emit(self))

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, options={self.options})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
