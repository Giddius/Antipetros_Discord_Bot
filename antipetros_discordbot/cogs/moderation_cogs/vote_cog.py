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
from time import sleep, time
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
import threading
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
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_dict_items_iterator
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.engine.replacements import AntiPetrosFlagCommand, AntiPetrosBaseCommand, auto_meta_info_command

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

COG_NAME = "VoteCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


# region [Helper]


_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class VoteCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    WiP
    """
# region [ClassAttributes]
    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,)}

    required_config_data = dedent("""
                                    """).strip('\n')
    number_emojis = {0: '0️⃣',
                     1: '1️⃣',
                     2: '2️⃣',
                     3: '3️⃣',
                     4: '4️⃣',
                     5: '5️⃣',
                     6: '6️⃣',
                     7: '7️⃣',
                     8: '8️⃣',
                     9: '9️⃣',
                     10: '🔟'}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.running_votes = []
        self.reaction_deques = {}

        glog.class_init_notification(log, self)

# endregion [Init]


# region [Properties]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        self.check_vote_ended_loop.start()
        self.remove_reaction_from_deques.start()

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(seconds=5)
    async def check_vote_ended_loop(self):
        for vote_item in self.running_votes:
            vote_message, vote_end_datetime, vote_dict = vote_item
            if vote_end_datetime <= datetime.utcnow():
                log.debug("end of vote found for %s", vote_end_datetime.isoformat(timespec="seconds"))
                await self._end_vote(vote_message, vote_dict)
                self.running_votes.remove(vote_item)

    @tasks.loop(seconds=1)
    async def remove_reaction_from_deques(self):
        async for message, value in async_dict_items_iterator(self.reaction_deques):
            async for user, reaction_deque in async_dict_items_iterator(value):
                while len(reaction_deque) > 1:
                    reaction = reaction_deque.popleft()
                    await reaction.remove(user)

    # async def remove_reaction_worker(self):
    #     log.debug('starting "reaction_removal_loop"')
    #     while True:
    #         for message, value in self.reaction_deques.items():
    #             for user, reaction_deque in value.items():
    #                 while len(reaction_deque) > 1:
    #                     log.debug("more than one item in deque")
    #                     reaction = reaction_deque.popleft()
    #                     await reaction.remove(user)


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name='on_reaction_add')
    async def vote_reaction_listener(self, reaction: discord.Reaction, user: Union[discord.User, discord.Member]):

        if user.bot is True:
            return

        if reaction.message not in {data[0] for data in self.running_votes}:
            return

        message_vote_reactions = [data[2] for data in self.running_votes if data[0].id == reaction.message.id][0]
        if str(reaction) not in message_vote_reactions:
            await reaction.clear()
            return
        if reaction.custom_emoji is True:
            return

        if user not in self.reaction_deques[reaction.message]:
            self.reaction_deques[reaction.message][user] = deque()
        self.reaction_deques[reaction.message][user].append(reaction)

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    @log_invoker(log, 'info')
    async def create_vote(self, ctx: commands.Context, title: str, description: str, run_for: int, *options: str):
        if len(options) > 10:
            await ctx.send(f'Too many options (`{len(options)}`)!\nMax amount of options is 10', delete_after=120, allowed_mentions=discord.AllowedMentions.none())
            await delete_message_if_text_channel(ctx)
            return
        fields = []
        vote_emojis = []
        end_datetime = datetime.utcnow() + timedelta(seconds=run_for)
        for index, option in enumerate(options):
            vote_emojis.append(self.number_emojis.get(index + 1))
            fields.append(self.bot.field_item(name=f"{self.number_emojis.get(index + 1)} ⇒ {option}", value=ZERO_WIDTH))
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=description,
                                                       fields=fields,
                                                       footer={'text': f"Vote is running for {run_for} seconds.\nUntil {end_datetime.strftime(self.bot.std_date_time_format)} UTC"},
                                                       thumbnail="vote")
        vote_message = await ctx.send(**embed_data)
        for vote_emoji in vote_emojis:
            await vote_message.add_reaction(vote_emoji)
        vote_dict = {v_emoji: option for v_emoji, option in zip(vote_emojis, options)}

        self.running_votes.append((vote_message, end_datetime, vote_dict))
        self.reaction_deques[vote_message] = {}

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    async def remove_other_reactions(self, reaction: discord.Reaction, user: Union[discord.User, discord.Member]):
        msg = await reaction.message.channel.fetch_message(reaction.message.id)
        log.info("current reactions on the message: %s", [str(m_reaction) for m_reaction in msg.reactions])
        for other_reaction in (m_reaction for m_reaction in msg.reactions if str(m_reaction) != str(reaction)):
            if user in await other_reaction.users().flatten():
                await other_reaction.remove(user)

    async def _end_vote(self, vote_message: discord.Message, vote_dict: dict):
        votes = {option_name: [] for vote_emoji, option_name in vote_dict.items()}
        vote_counts = {option_name: 0 for vote_emoji, option_name in vote_dict.items()}
        log.debug("fetching message")
        vote_message = await vote_message.channel.fetch_message(vote_message.id)
        log.debug("message fetched")

        for user, reaction_deque in self.reaction_deques[vote_message].items():
            reaction = reaction_deque.pop()
            if str(reaction) in vote_dict:

                option_name = vote_dict.get(str(reaction))
                vote_counts[option_name] += 1
                votes[option_name].append(user.mention)
        text = ""
        for option, user_mentions in votes.items():
            text += f"__**{option}**__\n"
            text += f"**Votes:** `{vote_counts.get(option)}`\n\n"
            for user_mention in user_mentions:
                text += f"{user_mention}\n"
            text += '\n\n\n'
        await vote_message.channel.send(text, allowed_mentions=discord.AllowedMentions.none())
        if vote_message.channel.type is discord.ChannelType.text:
            await self._modify_vote_message_with_result(vote_message, votes, vote_counts)
        del self.reaction_deques[vote_message]

    async def _modify_vote_message_with_result(self, vote_message: discord.Message, vote_users: dict, vote_counts: dict):
        embed = vote_message.embeds[0].copy()
        embed.clear_fields()
        embed.set_footer(text="**FINISHED**")
        for option_name, user_mentions in vote_users.items():
            embed.add_field(name=option_name, value=f"__Amount of Votes:__ {vote_counts.get(option_name)}\n\n" + '\n'.join(user_mentions), inline=False)
        await vote_message.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        for reaction in vote_message.reactions:
            await reaction.clear()

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
        self.check_vote_ended_loop.stop()
        self.remove_reaction_from_deques.stop()
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
    bot.add_cog(attribute_checker(VoteCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
