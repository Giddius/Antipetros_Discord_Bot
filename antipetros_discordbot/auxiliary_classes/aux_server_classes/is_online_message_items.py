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
from typing import Union, Callable, Iterable, TYPE_CHECKING, List, Optional
import inspect
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


import discord
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.auxiliary_classes.aux_server_classes.helper import ServerStatus, ServerStatusDeque, DelayedLock, DelayedSemaphore
from antipetros_discordbot.utility.discord_markdown_helper import ZERO_WIDTH
from antipetros_discordbot.utility.exceptions import AskCanceledError, AskTimeoutError
import gidlogger as glog
if TYPE_CHECKING:
    from antipetros_discordbot.auxiliary_classes.aux_server_classes.server_item import ServerItem, LogFileItem
    from antipetros_discordbot.cogs.antistasi_tool_cogs.community_server_info_cog import CommunityServerInfoCog
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


class IsOnlineHeaderMessage:
    db = general_db
    cog: "CommunityServerInfoCog" = None
    name = "is_online_header_message"

    def __init__(self, message: discord.Message = None) -> None:
        self.message = message

    async def exists(self):
        if self.message is None:
            return False
        try:
            await self.cog.is_online_messages_channel.fetch_message(self.message.id)
            return True
        except discord.errors.NotFound:
            await self.db.delete_misc_message(self.name)
            return False

    @classmethod
    async def load(cls):
        message = await cls._try_get_message()
        if message is None:
            log.debug("%s not found", cls.name)
        return cls(message=message)

    @classmethod
    async def _try_get_message(cls):
        message_data = await cls.db.get_misc_message_by_name(name=cls.name)

        if message_data is None:
            return None
        message_id = message_data.get('message_id')
        try:
            return await cls.cog.is_online_messages_channel.fetch_message(message_id)
        except discord.errors.NotFound:
            return None

    @property
    def request_restart_action_enabled(self):
        return COGS_CONFIG.retrieve(self.cog.config_name, 'request_restart_interaction_enabled', typus=bool, direct_fallback=False)

    @property
    def default_description(self):
        text = inspect.cleandoc(f"""
                __Interactions__

                > An Emoji under the server status messages means one of the following interactions is possible:

                • {str(self.cog.is_online_interaction_emojis.get('request_mod_data'))}

                > You can request the current mod data for this Server.
                > The Bot will send you an DM with the mod data info and an HTML file, that you can Drag and Drop onto the ARMA 3 shortcut to automatically enable the specified mods.
                """)

        if self.request_restart_action_enabled is True:
            text += '\n\n' + inspect.cleandoc(f"""
                • {str(self.cog.is_online_interaction_emojis.get('request_restart'))} ***[EXPERIMENTAL]***

                > You can request an restart for this Server.
                > The Bot will DM you with some questions regarding that restart request.
                > You can abort the request at any stage of the questions and before sending it the bot will ask you to confirm if you really want to send the request.
                """)
        return text

    @property
    def is_online_messages_channel(self):
        return self.cog.is_online_messages_channel

    @property
    def teamspeak_server_addresses(self):
        return COGS_CONFIG.retrieve(self.cog.config_name, 'teamspeak_server_addresses', typus=List[str], direct_fallback=["38.65.5.151", "antistasi.armahosts.com"])

    @property
    def description(self):
        return COGS_CONFIG.retrieve(self.cog.config_name, 'is_online_message_header_description', typus=str, direct_fallback=self.default_description)

    async def _embed_kwargs(self):
        return {'title': self.is_online_messages_channel.name.replace('-', ' ').replace('_', ' ').title(),
                'description': self.description,
                "thumbnail": "https://i.postimg.cc/YS5dNy1v/cog-icon.png",
                'footer': 'armahosts',
                "url": self.cog.bot.antistasi_url,
                "fields": [EmbedFieldItem(name="Teamspeak Server Address", value=' **OR** '.join(f"`{item}`" for item in self.teamspeak_server_addresses), inline=False)],
                "author": 'default'}

    async def _embed_data(self):
        embed_kwargs = await self._embed_kwargs()
        return await self.cog.bot.make_generic_embed(**embed_kwargs)

    async def remove(self):
        exists = await self.exists()
        if exists is True:
            await self.message.delete()
            self.message = None
            await self.db.delete_misc_message(name=self.name)

    async def create(self):
        if any([await server.is_online_message.exists() is True for server in self.cog.server_items]):
            log.warning("At least one is online message higher than the header, redoing all!")
            await asyncio.gather(*[server.is_online_message.remove() for server in self.cog.server_items])

        embed_data = await self._embed_data()
        self.message = await self.is_online_messages_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await self.cog.db.insert_misc_message(misc_message=self.message, name=self.name)

    async def _update_embed(self):
        embed_data = await self._embed_data()
        await self.message.edit(embed=embed_data.get('embed'), allowed_mentions=discord.AllowedMentions.none())

    async def update(self):
        log.info("Updating is_online_message_header")
        exists = await self.exists()

        if exists is False:
            await self.create()

        else:
            await self._update_embed()

        await self.clean_reactions()

    async def clean_reactions(self):
        log.debug("cleaning reactions from is_online_header")
        if self.message is not None:
            await self.message.clear_reactions()


class IsOnlineMessage:
    cog: "CommunityServerInfoCog" = None
    db = general_db

    def __init__(self, server: "ServerItem", message: discord.Message = None):
        self.server = server
        self.message = message

    @property
    def mod_data_emoji(self):
        return self.cog.is_online_interaction_emojis["request_mod_data"]

    @property
    def restart_emoji(self):
        return self.cog.is_online_interaction_emojis["request_restart"]

    @property
    def emoji_actions(self):
        return {str(self.mod_data_emoji): self._send_mod_data,
                str(self.restart_emoji): self._start_restart_questions}

    @property
    def request_restart_action_enabled(self):
        return COGS_CONFIG.retrieve(self.cog.config_name, 'request_restart_interaction_enabled', typus=bool, direct_fallback=False)

    @classmethod
    async def load(cls, server: "ServerItem"):
        if cls.cog is None:
            cls.cog = server.cog
        message_id = await cls.db.get_is_online_message_id(server=server)
        message = await cls._try_get_message(message_id=message_id)
        if message is None:
            log.debug("is_online_message for server %s not found", server.name)
        return cls(server=server, message=message)

    @classmethod
    async def _try_get_message(cls, message_id: Union[int, None]) -> Union[None, discord.Message]:
        if message_id is None:
            return None
        try:
            return await cls.cog.is_online_messages_channel.fetch_message(message_id)
        except discord.errors.NotFound:
            return None

    @property
    def is_online_messages_channel(self):
        return self.cog.is_online_messages_channel

    @property
    def emojis(self) -> list[Union[discord.Emoji, str]]:
        emojis = []
        if self.online_status is ServerStatus.ON:
            if self.server.has_access_to_logs is True:
                emojis.append(self.mod_data_emoji)
            if self.request_restart_action_enabled is True:
                emojis.append(self.restart_emoji)
        return emojis

    @property
    def enabled(self):
        return self.server.is_online_message_enabled

    @property
    def online_status(self):
        return self.server.current_status

    @property
    def thumbnail(self):
        return self.server.thumbnail

    @property
    def description(self):
        return ZERO_WIDTH

    async def exists(self):
        if self.message is None:
            return False
        try:
            await self.cog.is_online_messages_channel.fetch_message(self.message.id)
            return True
        except discord.errors.NotFound:
            await self.db.remove_is_online_message(self)
            return False

    async def _get_embed_fields(self):
        embed_fields = []
        if self.online_status is None:
            await self.server.is_online()
        if self.online_status is ServerStatus.OFF:
            embed_fields.append(EmbedFieldItem(name="Is __OFFLINE__", value=ZERO_WIDTH, inline=True))
            embed_fields.append(EmbedFieldItem(name="ON", value="❌", inline=True))
            return embed_fields

        info_data = await self.server.get_info()

        embed_fields.append(EmbedFieldItem(name="ON", value="☑️", inline=True))
        embed_fields.append(EmbedFieldItem(name="Server Address", value=self.server.server_address.url, inline=True))
        embed_fields.append(EmbedFieldItem(name="Port", value=self.server.server_address.port, inline=True))
        embed_fields.append(EmbedFieldItem(name="Players", value=f"{info_data.player_count}/{info_data.max_players}", inline=True))
        embed_fields.append(EmbedFieldItem(name="Map", value=info_data.map_name, inline=True))

        if self.server.has_access_to_logs is True:
            last_restarted_pretty = await self.server.get_last_restarted_at_pretty()
            if last_restarted_pretty is not None:
                embed_fields.append(EmbedFieldItem(name="Last Restart", value=last_restarted_pretty, inline=False))

        return embed_fields

    async def _embed_kwargs(self):
        footer = self.cog.bot.special_footers.get('armahosts', {}).copy()
        footer['text'] = f"{footer.get('text','')}\nLast updated ☛"

        return {"author": "default_author",
                "title": self.server.official_name,
                "description": self.description,
                "url": self.server.battle_metrics_url,
                "footer": footer,
                "fields": await self._get_embed_fields(),
                "color": self.server.color,
                "timestamp": datetime.now(timezone.utc),
                "thumbnail": self.thumbnail}

    async def _embed_data(self):
        embed_kwargs = await self._embed_kwargs()
        return await self.cog.bot.make_generic_embed(**embed_kwargs)

    async def create(self):
        embed_data = await self._embed_data()
        self.message = await self.is_online_messages_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await self.db.insert_is_online_message(self)

    async def remove(self, exists: bool = None):
        exists = exists if exists is not None else await self.exists()
        if exists is True:
            await self.message.delete()
            self.message = None
            await self.db.remove_is_online_message(self)

    async def _update_embed(self):
        embed_data = await self._embed_data()
        await self.message.edit(embed=embed_data.get('embed'), allowed_mentions=discord.AllowedMentions.none())

    async def update(self):
        log.info("Updating is_online_message of server %s", self.server.name)
        exists = await self.exists()
        if self.enabled is False:
            await self.remove(exists=exists)
            return

        if exists is False:
            await self.create()

        else:
            await self._update_embed()
        await self._add_emojis()
        await self.clean_reactions()

    async def _add_emojis(self):
        for emoji in self.emojis:
            await self.message.add_reaction(emoji=emoji)

    async def handle_reaction(self, reaction: Union[str, discord.PartialEmoji, discord.Emoji], member: discord.Member):

        log.debug("handle_reaction triggered for Server %s, by: reaction=%s, member=%s", self.server.name, reaction, member)

        if await self.cog.bot.other_check_blocked(member) is True:
            log.warning("User %s is blacklisted", member)
            return

        if str(reaction) in {str(emoji) for emoji in self.emojis}:
            action = self.emoji_actions.get(str(reaction))
            log.debug("reaction '%s', is in action_emojis, for Server %s, triggering action: '%s'", reaction, self.server.name, action.__name__)

            await action(member=member)
        else:
            log.debug("reaction %s is not in self.emojis(%s)", reaction, self.emojis)

        await self.clean_reactions(reaction=reaction, member=member)

    async def clean_reactions(self, reaction: Union[str, discord.Emoji, discord.PartialEmoji] = None, member: Union[discord.User, discord.Member] = None):
        log.debug("Starting to clean emojis from is_online_message of server %s", self.server.name)
        emojis = {str(emoji) for emoji in self.emojis}
        if reaction is not None and str(reaction) not in emojis:
            await self.message.clear_reaction(emoji=reaction)
        elif reaction is not None and member is not None:
            await self.message.remove_reaction(emoji=reaction, member=member)

        for message_reaction in self.message.reactions:
            if str(message_reaction) not in emojis:
                await self.message.clear_reaction(emoji=message_reaction)
            async for user in message_reaction.users():
                if user.id != self.cog.bot.id or str(message_reaction) not in emojis:
                    log.debug("trying to remove reaction %s, by user %s from is_online_mesage for server %s", reaction, user, self.server.name)
                    await self.message.remove_reaction(emoji=message_reaction, member=user)

    async def _send_mod_data(self, member: discord.Member):
        try:
            mod_data = await self.server.get_mod_files()
            embed_data = await self.cog.bot.make_generic_embed(title=self.server.official_name,
                                                               description=ZERO_WIDTH,
                                                               thumbnail=self.thumbnail,
                                                               image=mod_data.image,
                                                               author="armahosts",
                                                               footer="armahosts",
                                                               color="blue",
                                                               url=self.server.battle_metrics_url)
            embed_data['files'].append(mod_data.html)
            msg = await member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
            await msg.add_reaction(self.cog.bot.armahosts_emoji)
        except IndexError as e:
            log.error(e, exc_info=True)
            log.warning("Requesting log files to dm lead to an IndexError with Server %s", self.server.name)

            asyncio.create_task(self.server.gather_log_items())
            await member.send("Sorry there was an Error in getting the Mod data, please try again in a minute or so", allowed_mentions=discord.AllowedMentions.none())
        await self.cog.add_to_amount_mod_data_requested()

    async def _start_restart_questions(self, member: discord.Member):
        try:
            await self.cog._handle_restart_request(member=member, server_item=self.server)

        except AskCanceledError:
            log.debug("restart request was canceled")
        except AskTimeoutError:
            log.debug("restart request was timedout")
        await self.cog.add_to_amount_restart_requested()

    def __str__(self):
        return f"{self.__class__.__name__}(server={self.server.name}, message={self.message}, emojis={self.emojis}, is_online_messages_channel={self.is_online_messages_channel.name}, enabled={self.enabled}, online_status={self.online_status})"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
