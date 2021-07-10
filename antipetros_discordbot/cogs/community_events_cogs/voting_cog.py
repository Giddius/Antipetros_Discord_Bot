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

from antipetros_discordbot.engine.replacements.task_loop_replacement import custom_loop
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

import pyparsing as pp
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_write_json, async_load_json
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker, Seperators
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI, letter_to_emoji, CANCEL_EMOJI
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler
from PIL import Image
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import shorten_string
from antipetros_discordbot.abstracts.connect_signal import AbstractConnectSignal
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


from antipetros_discordbot.auxiliary_classes.voting_items import VoteOptionItem, VoteItem, VoteStartedSignal
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


# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    def _init_items(self):
        VoteItem.bot = self.bot
        VoteItem.vote_started_signal.connect(self._add_to_running_votes)

    async def on_ready_setup(self):
        await super().on_ready_setup()
        self._init_items()
        VoteItem.bot = self.bot
        self.ready = True

    async def update(self, typus: UpdateTypus):
        await super().update(typus)
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @custom_loop(minutes=5)
    async def remove_finished_votes(self):
        if self.completely_ready is False:
            return
        to_remove = []
        for vote in self.running_votes:
            if vote.finished is True:
                to_remove.append(vote)
        for finished_vote in to_remove:
            log.debug("removing finished vote %s", finished_vote)
            self.running_votes.remove(finished_vote)

        log.debug("running votes: %s", self.running_votes)

# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def check_for_vote_listener(self, payload: discord.RawReactionActionEvent):
        if self.completely_ready is False:
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


    async def _parse_options_line(self, options_line: str):
        _out = []
        for part in options_line.split(';'):
            part = part.strip()
            if part != "":
                _out.append(VoteOptionItem.from_text(part))
        return _out

    @auto_meta_info_command(clear_invocation=True, confirm_command_received=True)
    async def new_vote(self, ctx: commands.Context, minutes: int, name: str, *, options_line: str):
        """
        Creates a generic new Vote.

        This is the vote command has full control over the options for the vote.

        Args:
            minutes (int): How many minutes the vote should run.
            name (str): The name of the vote, this is also the title of the vote embed. Needs to be in quotes if it contains spaces.
            options_line (str): the options for the vote, seperated by a semi-colon (;) in the format: option_name == emoji. If no emoji is specified, then an emoji is auto-assigned.No quotes needed.

        Example:
            @AntiPetros new-vote 15 "my vote title" first item == 🌞; second item == 🎡; item with auto emoji;
        """
        vote = VoteItem(name=name, options=await self._parse_options_line(options_line), end_at=datetime.now(tz=timezone.utc) + timedelta(minutes=minutes), after_report=True, report_each_vote=True)
        await vote.start_vote(ctx.channel)

    @auto_meta_info_command(clear_invocation=True, confirm_command_received=True)
    async def member_vote(self, ctx: commands.Context, member: discord.Member, minutes: int = 10):
        options = [VoteOptionItem(item="YES", emoji=CHECK_MARK_BUTTON_EMOJI),
                   VoteOptionItem(item="NO", emoji=CROSS_MARK_BUTTON_EMOJI),
                   VoteOptionItem(item="MORE TIME NEEDED", emoji="🕑")]
        allowed_roles = [self.bot.get_antistasi_role(449549800879423488)]  # Role_id = Members
        vote = VoteItem(name=f"Membership Vote for {member.display_name}", options=options, end_at=self.minutes_to_end_datetime(minutes), allowed_roles=allowed_roles, after_report=True, report_each_vote=True, show_each_vote=True)
        vote.set_thumbnail(str(member.avatar_url))

        battlemetrics_link = ""
        joined_at = member.joined_at.strftime(self.bot.std_date_time_format) + ' UTC'
        vote.set_description(f"{member.mention}\nJoined this Guild at: `{joined_at}`\n{battlemetrics_link}")
        await vote.start_vote(ctx.channel)

    @auto_meta_info_command(clear_invocation=True, confirm_command_received=True)
    async def cancel_vote(self, ctx: commands.Context):
        vote = await self.get_running_vote_by_reference(ctx)
        if vote is None:
            await ctx.send('Unable to find vote', delete_after=90)
            return
        await vote.cancel_vote()

    @auto_meta_info_command(clear_invocation=True, confirm_command_received=True)
    async def add_time_to_vote(self, ctx: commands.Context, minutes: int):
        vote = await self.get_running_vote_by_reference(ctx)

        to_add_time = timedelta(minutes=minutes)
        vote.end_at += to_add_time
        await vote.update_embed()

    @auto_meta_info_command(clear_invocation=True, confirm_command_received=True)
    async def finish_vote(self, ctx: commands.Context):
        vote = await self.get_running_vote_by_reference(ctx)
        if vote is None:
            await ctx.send('Unable to find vote', delete_after=90)
            return
        await vote.finish_vote()

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def get_running_vote_by_reference(self, ctx: commands.Context) -> VoteItem:
        reference_message = ctx.message.reference.resolved
        return await self.get_running_vote_by_message(reference_message)

    async def get_running_vote_by_message(self, message: discord.Message) -> VoteItem:
        vote_dict = {running_vote.vote_message: running_vote for running_vote in self.running_votes}
        vote = await asyncio.sleep(0, vote_dict.get(message, None))
        return vote

    async def _add_to_running_votes(self, vote: VoteItem):
        self.running_votes.add(vote)

    def minutes_to_end_datetime(self, minutes: int) -> datetime:
        delta = timedelta(minutes=minutes)
        return datetime.now(tz=timezone.utc) + delta


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
