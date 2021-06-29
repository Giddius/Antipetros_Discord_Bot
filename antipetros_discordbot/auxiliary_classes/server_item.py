"""
[summary]

[extended_summary]
"""

# region [Imports]


import gc
from copy import deepcopy
import asyncio
import unicodedata
import discord
from enum import Enum, auto, unique
import os
from textwrap import indent, dedent
import re
from asyncstdlib import map as async_map
from typing import TYPE_CHECKING, Union, Iterable, Callable, Any, IO, Optional, List, Tuple, Set, Dict
from datetime import datetime, timezone
from functools import cached_property, total_ordering
from dateparser import parse as date_parse
from collections import namedtuple, deque
from async_property import async_property, async_cached_property
from aiodav import Client as AioWebdavClient
from aiodav.client import Resource
import gidlogger as glog
from asyncio import Lock as AioLock
from asyncstdlib import lru_cache as async_lru_cache
from antipetros_discordbot.utility.gidtools_functions import bytes2human, loadjson, readit, pathmaker, writejson

from antipetros_discordbot.utility.regexes import LOG_SPLIT_REGEX, MOD_TABLE_END_REGEX, MOD_TABLE_LINE_REGEX, MOD_TABLE_START_REGEX, REAL_LOG_TIME_REGEX
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.misc import SIZE_CONV_BY_SHORT_NAME, alt_seconds_to_pretty
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from jinja2 import Environment, FileSystemLoader, BaseLoader
from io import BytesIO
import a2s
from weasyprint import HTML
import aiohttp
import inspect
from aiodav.exceptions import NoConnection
from sortedcontainers import SortedDict, SortedList
from marshmallow import Schema, fields
from hashlib import shake_256
if TYPE_CHECKING:
    from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog
    from antipetros_discordbot.cogs.antistasi_tool_cogs.community_server_info_cog import CommunityServerInfoCog
from zipfile import ZipFile, ZIP_LZMA
from antipetros_discordbot.abstracts.connect_signal import AbstractConnectSignal
from antipetros_discordbot.utility.exceptions import AskCanceledError, AskTimeoutError
from pyparsing import (Word, alphanums, punc8bit, alphas, Literal, Optional, OneOrMore, oneOf, Group, nums, nestedExpr, delimitedList,
                       dblQuotedString, quotedString, Forward, Suppress, SkipTo, ZeroOrMore, Combine, Regex, Keyword, CaselessLiteral,
                       restOfLine, ParserElement, countedArray, CharsNotIn, cStyleComment, commaSeparatedList, cppStyleComment, LineEnd,
                       LineStart, NotAny, removeQuotes, nestedExpr, CaselessKeyword, CaselessLiteral, FollowedBy)

import pyparsing as pp

from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.utility.asyncio_helper import async_range
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


ModFileItem = namedtuple('ModFileItem', ['html', 'image'])


class DelayedLock(asyncio.Lock):

    def __init__(self, delay: float = 1) -> None:
        super().__init__()
        self.delay = delay

    def release(self) -> None:
        asyncio.create_task(self._release_task())

    async def _release_task(self) -> None:
        await asyncio.sleep(self.delay)
        return super().release()


class DelayedSemaphore(asyncio.Semaphore):

    def __init__(self, value: int, delay: float = 1) -> None:
        super().__init__(value=value)
        self.delay = delay

    def release(self) -> None:
        asyncio.create_task(self._release_task())

    async def _release_task(self) -> None:
        await asyncio.sleep(self.delay)
        return super().release()


@unique
class ServerStatus(Enum):
    ON = auto()
    OFF = auto()

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, bool):
            if value is True:
                return cls.ON
            return cls.OFF
        return super()._missing_(value)


class ServerStatusDeque(deque):

    def __init__(self) -> None:
        super().__init__(iterable=[None, None], maxlen=2)

    @property
    def current_status(self) -> ServerStatus:
        return self[1]

    @property
    def previous_status(self) -> ServerStatus:
        return self[0]

    async def add_new_status(self, status: ServerStatus):
        self.append(status)
        has_changed = await self._check_changed()
        log.debug("added new status, status has changed = %s", has_changed)
        return has_changed

    async def _check_changed(self):
        if None in self:
            return False
        return len(set(self)) != 1


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
        message_id = message_data.get('message_id')
        if message_id is None:
            return None
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
            self.cog.amount_mod_data_requested += 1

    async def _start_restart_questions(self, member: discord.Member):
        try:
            await self.cog._handle_restart_request(member=member, server_item=self.server)
            self.cog.amount_restart_requested += 1
        except AskCanceledError:
            log.debug("restart request was canceled")
        except AskTimeoutError:
            log.debug("restart request was timedout")

    def __str__(self):
        return f"{self.__class__.__name__}(server={self.server.name}, message={self.message}, emojis={self.emojis}, is_online_messages_channel={self.is_online_messages_channel.name}, enabled={self.enabled}, online_status={self.online_status})"


@ unique
class AntistasiSide(Enum):
    GREENFOR = auto()
    BLUFOR = auto()
    REDFOR = auto()
    CIV = auto()


class StatusSwitchSignal(AbstractConnectSignal):

    async def emit(self, server: "ServerItem", switched_to: ServerStatus):
        await super().emit(server, switched_to)


class NewCampaignSignal(AbstractConnectSignal):

    async def emit(self, server: "ServerItem", map_name: str, mission_type: str):
        await super().emit(server, map_name, mission_type)


class FlagCapturedSignal(AbstractConnectSignal):
    async def emit(self, server: "ServerItem", flag_name: str, switched_to: AntistasiSide):
        return await super().emit(server, flag_name, switched_to)


def fix_path(in_path: str) -> str:
    path_parts = in_path.split('/')
    fixed_path = '/' + '/'.join(path_parts[-4:])
    return fixed_path


def fix_info_dict(info_dict: dict) -> dict:
    _ = info_dict.pop('path', None)
    _ = info_dict.pop('isdir', None)
    return info_dict


def _transform_mod_name(mod_name: str):
    mod_name = mod_name.removeprefix('@')
    return mod_name


pre_data_regex = re.compile(r"\={5,}.*?\={5,}", re.DOTALL)
start_point_regex = re.compile(r"\d{4}/\d{2}/\d{2}\,\s\d{2}\:\d{2}\:\d{2}.*")
newline_fix_regex = re.compile(r"\n\s*(?!\d{4}/\d{2}/\d{2}\,\s\d{2}\:\d{2}\:\d{2})")
array_fix_regex = re.compile(r"((?<=\])\s*(?=\[))")
array_ends_fix_regex = re.compile(r"((?<=\])\s*(?=\]))|((?<=\[)\s*(?=\[))")
pre_whitespace_regex = re.compile(r"(?<=\d{4}/\d{2}/\d{2}\,\s\d{2}\:\d{2}\:\d{2})\s{2,}")


def clean_log_text(text: str):
    text = pre_data_regex.sub("", text, 1)
    text = text[start_point_regex.search(text).start():]
    text = newline_fix_regex.sub(" ", text)
    text = array_fix_regex.sub(", ", text)
    text = array_ends_fix_regex.sub("", text)
    text = pre_whitespace_regex.sub(" ", text)
    return text


def log_grammar():
    year = Word(nums)
    month = Word(nums)
    day = Word(nums)

    hour = Word(nums)
    minute = Word(nums)
    second = Word(nums)
    nano_second = Word(nums)

    separator = Suppress('|')

    antistasi_identifier = Suppress('Antistasi')

    level = oneOf('Debug Info Error Warning')("log_level")

    function = Suppress('File:') + Word(alphanums + '_')("function_name")

    space = Suppress(' ')

    message = ZeroOrMore(space) + restOfLine('message')

    useless_datetime = Suppress(year + '/' + month + '/' + day + ', ' + hour + ':' + minute + ':' + second)

    datetime_stamp = (year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second + ':' + nano_second)

    antistasi_log_line = useless_datetime + Combine(datetime_stamp)("datetime_stamp") + separator + antistasi_identifier + separator + level + separator + function + separator + message

    return antistasi_log_line


class LogParser:
    new_campaign = NewCampaignSignal()
    flag_captured = FlagCapturedSignal()
    lock = DelayedLock(delay=0.1)

    def __init__(self, server_item: "ServerItem") -> None:
        self._mod_lookup_data = None
        self.server = server_item
        self.current_log_item = None
        self.current_byte_position = 0
        self.jinja_env = Environment(loader=BaseLoader, enable_async=True)
        self._parsed_data = None

    @ property
    def mod_lookup_data(self):
        if self._mod_lookup_data is None:
            if os.path.isfile(pathmaker(APPDATA['fixed_data'], 'mod_lookup.json')) is False:
                writejson({}, pathmaker(APPDATA['fixed_data'], 'mod_lookup.json'))
            self._mod_lookup_data = loadjson(APPDATA['mod_lookup.json'])
        return self._mod_lookup_data

    def reset(self):
        self._parsed_data = None
        self._mod_lookup_data = None

    async def _parse_mod_data(self) -> list:
        if self._parsed_data is None:
            _out = []
            current_content_bytes = []
            async with self.lock:
                async for chunk in await self.server.newest_log_item.content_iter():
                    current_content_bytes.append(chunk)
            current_content = b''.join(current_content_bytes).decode('utf-8', errors='ignore')
            split_match = await asyncio.to_thread(LOG_SPLIT_REGEX.search, current_content)
            if split_match:
                pre_content = current_content[:split_match.end()]
                cleaned_lower = await asyncio.to_thread(MOD_TABLE_START_REGEX.split, pre_content)
                cleaned_lower = cleaned_lower[-1]
                mod_table = await asyncio.to_thread(MOD_TABLE_END_REGEX.split, cleaned_lower)
                mod_table = mod_table[0]
                for line in mod_table.splitlines():
                    if line != '':
                        line_match = await asyncio.to_thread(MOD_TABLE_LINE_REGEX.search, line)
                        _out.append({key: value.strip() for key, value in line_match.groupdict().items()})
                    await asyncio.sleep(0)

                items = [item.get('mod_dir') for item in _out if item.get('official') == 'false' and item.get("mod_name") not in {"@members", "@TaskForceEnforcer", "@utility"}]
                self._parsed_data = sorted(items)
        return self._parsed_data

    async def _render_mod_data(self) -> str:
        mod_data = await self._parse_mod_data()
        try:
            templ_data = []
            for item in mod_data:
                transformed_mod_name = await asyncio.sleep(0, _transform_mod_name(item))
                templ_data.append(self.mod_lookup_data.get(transformed_mod_name))

            return await self.mod_template.render_async(req_mods=templ_data, server_name=self.server.name.replace('_', ' '))
        except TypeError as error:
            log.critical("'%s', when parsing mod-data for Server '%s', for file '%s'", error, self.server.name, self.server.newest_log_item.name)
            raise error

    async def get_mod_data_html_file(self) -> discord.File:
        with BytesIO() as bytefile:
            html_string = await self._render_mod_data()
            bytefile.write(html_string.encode('utf-8', errors='ignore'))
            bytefile.seek(0)
            return discord.File(bytefile, f"{self.server.name}_mods.html")

    async def get_mod_data_image_file(self) -> discord.File:
        html_string = await self._render_mod_data()
        weasy_html = await asyncio.to_thread(HTML, string=html_string)
        with BytesIO() as bytefile:
            await asyncio.to_thread(weasy_html.write_png, bytefile, optimize_images=False, presentational_hints=False, resolution=96)
            bytefile.seek(0)
            return discord.File(bytefile, f"{self.server.name}_mods.png")

    async def get_only_level(self, level: str):
        _out = []
        current_content_bytes = []
        async for chunk in await self.server.newest_log_item.content_iter():
            current_content_bytes.append(chunk)
        current_content = b''.join(current_content_bytes).decode('utf-8', errors='ignore')
        text = await asyncio.to_thread(clean_log_text, current_content)
        grammar = log_grammar()
        items = await asyncio.to_thread(grammar.searchString, text)
        for item in items:
            data = await asyncio.to_thread(item.asDict)
            if data.get('log_level', '').casefold() == level.casefold():
                _out.append(' | '.join(item))

        return '\n'.join(_out)

    @ property
    def mod_template(self):
        template_string = readit(APPDATA["arma_required_mods.html.jinja"])
        return self.jinja_env.from_string(template_string)

    def __repr__(self) -> str:
        return self.__class__.__name__


class LogFileSchema(Schema):
    server = fields.Nested("ServerSchema", exclude=('log_items',))

    class Meta:
        additional = ("path", "name", "info", "exists", 'size', 'size_pretty', 'created', 'modified', 'created_pretty', 'modified_pretty', 'is_over_threshold', 'etag', 'created_in_seconds')


class ServerSchema(Schema):
    log_items = fields.List(fields.Nested(LogFileSchema, exclude=('server',)))
    previous_status = fields.String()
    newest_log_item = fields.Nested(LogFileSchema, exclude=('server',))
    server_address = fields.String()
    log_parser = fields.String()

    class Meta:
        additional = ('name', 'log_folder', 'config_name', 'sub_log_folder_name', 'base_log_folder_name', 'log_folder_path', 'report_status_change')


@ total_ordering
class LogFileItem:
    config_name = None
    size_string_regex = re.compile(r"(?P<number>\d+)\s?(?P<unit>\w+)")
    log_name_regex = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
    schema = LogFileSchema()

    semaphore = DelayedSemaphore(1)

    time_pretty_format = "%Y-%m-%d %H:%M:%S UTC"
    hashfunc = shake_256

    def __init__(self, resource_item: Resource, info: dict, server_item: "ServerItem") -> None:
        self.server_item = server_item
        self.path = fix_path(info.get('path'))
        self.name = os.path.basename(self.path)
        self.resource_item = resource_item
        self.info = fix_info_dict(info)
        self.exists = True
        self.created = date_parse(self.info.get("created"), settings={'TIMEZONE': 'UTC'}) if self.info.get("created") is not None else self._date_time_from_name()
        self.created_in_seconds = int(self.created.timestamp())
        self.last_real_restart_time = None

    async def get_first_logged_correct_time(self):
        found = False
        if self.last_real_restart_time is None:
            async with self.semaphore:
                async for chunk in await self.content_iter():
                    if found is False:
                        time_match = REAL_LOG_TIME_REGEX.search(chunk.decode('utf-8', errors='ignore'))
                        if time_match:
                            self.last_real_restart_time = datetime(**{key: int(value) for key, value in time_match.groupdict().items()}).replace(tzinfo=timezone.utc)
                            log.debug("found real last restart datetime for server %s, as %s", self.server_item.name, self.last_real_restart_time)
                            found = True

        return self.last_real_restart_time

    async def collect_info(self) -> None:
        async with self.semaphore:
            self.info = await self.resource_item.info()
            await asyncio.sleep(0)

    async def update(self):
        return NotImplemented

    @ classmethod
    @ property
    def warning_size_threshold(cls) -> int:
        limit = COGS_CONFIG.retrieve(cls.config_name, 'log_file_warning_size_threshold', typus=str, direct_fallback='200mb')
        match_result = cls.size_string_regex.search(limit)
        relative_size = int(match_result.group('number'))
        unit = match_result.group('unit').casefold()
        return relative_size * SIZE_CONV_BY_SHORT_NAME.get(unit)

    @ property
    def etag(self) -> str:
        return self.info.get("etag").strip('"')

    @ property
    def modified(self) -> datetime:
        return date_parse(self.info.get("modified"), settings={'TIMEZONE': 'UTC'})

    @ property
    def size(self) -> int:
        return int(self.info.get("size"))

    @ property
    def size_pretty(self) -> str:
        return bytes2human(self.size, annotate=True)

    @ cached_property
    def created_pretty(self) -> str:
        return self.created.strftime(self.time_pretty_format)

    @ property
    def modified_pretty(self) -> str:
        return self.modified.strftime(self.time_pretty_format)

    @ property
    def is_over_threshold(self) -> bool:
        if self.size >= self.warning_size_threshold:
            return True
        return False

    def _date_time_from_name(self) -> datetime:
        matched_data = self.log_name_regex.search(os.path.basename(self.path))
        if matched_data:
            return datetime(**{key: int(value) for key, value in matched_data.groupdict().items()}, microsecond=0, tzinfo=timezone.utc)
        else:
            raise ValueError(f'unable to find date_time_string in {os.path.basename(self.path)}')

    async def content_iter(self):
        return await self.resource_item.client.download_iter(self.path)

    async def get_content(self):
        async with self.semaphore:
            byte_data = b""
            async for chunk in await self.content_iter():
                byte_data += chunk
            return byte_data.decode('utf-8', errors='ignore')

    async def content_embed(self):
        async with self.semaphore:
            await self.collect_info()

        with BytesIO() as bytefile:
            name = self.name.split('.')[0] + '.zip'
            if self.size > self.server_item.cog.bot.filesize_limit:
                with ZipFile(bytefile, 'w', ZIP_LZMA) as zippy:
                    content_bytes = b''
                    async with self.semaphore:
                        async for chunk in await self.content_iter():
                            content_bytes += chunk
                        zippy.writestr(self.name, content_bytes.decode('utf-8', 'ignore'))
            else:
                name = self.name
                async with self.semaphore:
                    async for chunk in await self.content_iter():
                        bytefile.write(chunk)
            bytefile.seek(0)
            _hash = self.hashfunc(bytefile.read()).hexdigest(8)
            bytefile.seek(0)
            file = discord.File(bytefile, name)
        embed_data = await self.server_item.cog.bot.make_generic_embed(title=self.name, fields=[self.server_item.cog.bot.field_item(name='Server', value=self.server_item.pretty_name, inline=False),
                                                                                                self.server_item.cog.bot.field_item(name='Size', value=self.size_pretty, inline=False),
                                                                                                self.server_item.cog.bot.field_item(name='Created', value=self.created_pretty, inline=False),
                                                                                                self.server_item.cog.bot.field_item(name='Last modified', value=self.modified_pretty, inline=False),
                                                                                                self.server_item.cog.bot.field_item(name='Hash', value=_hash, inline=False)],
                                                                       timestamp=self.modified,
                                                                       thumbnail=self.server_item.cog.server_logos.get(self.server_item.name.casefold(), 'no_thumbnail'),
                                                                       footer={'text': 'Last modified in your timezone, see timestamp ->'})

        embed_data['files'].append(file)
        return embed_data

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with path '{self.path}'"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" + ', '.join(map(str, [self.created_pretty, self.etag, self.modified_pretty, self.name, self.path, self.size, self.size_pretty])) + ')'

    def __hash__(self):
        return hash(self.name) + hash(self.created)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, LogFileItem):
            return hash(self) == hash(o)
        return NotImplemented

    def __le__(self, o: object) -> bool:
        if isinstance(o, LogFileItem):
            return o.created_in_seconds <= self.created_in_seconds
        return NotImplemented

    async def dump(self) -> dict:
        await self.collect_info()
        return self.schema.dump(self)


class ServerAddress:

    def __init__(self, full_address: str) -> None:
        self.full_address = full_address
        self.url = self.full_address.split(':')[0].strip()
        self.port = int(self.full_address.split(':')[1].strip())

    @ property
    def delta_query_port(self) -> int:
        return BASE_CONFIG.retrieve("arma", "delta_query_port", typus=int, direct_fallback=1)

    @ property
    def query_port(self):
        return self.port + self.delta_query_port

    @ property
    def query_address(self):
        return (self.url, self.query_port)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(url={self.url}, port={self.port}, query_port={self.query_port})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.full_address})"


class ServerItem:
    pretty_name_regex = re.compile(r"(?P<name>[a-z]+)\_?(?P<server>server)\_?(?P<number>\d)?", re.IGNORECASE)
    timeout = 5.0
    battlemetrics_base_url = "https://www.battlemetrics.com/servers/arma3"

    # TODO: Refactor into a "server_meta_data_mapping" from here
    battle_metrics_mapping = {'mainserver_1': "10560386",
                              'mainserver_2': "11460213",
                              'testserver_1': "4789978",
                              'testserver_2': "9851037",
                              'eventserver': "9552734",
                              'sog_server_1': "11406516",
                              'sog_server_2': "11406517"}

    server_priority_map = {"mainserver_1": 1,
                           "mainserver_2": 2,
                           "sog_server_1": 3,
                           "sog_server_2": 4,
                           "eventserver": 5,
                           "testserver_1": 6,
                           "testserver_2": 7}

    server_thumbnail_mapping = {'mainserver_1': {ServerStatus.ON: "https://i.postimg.cc/d0Y0krSc/mainserver-1-logo.png",
                                                 ServerStatus.OFF: 'https://i.postimg.cc/YSWHwSSB/mainserver-1-logo-off.png'},
                                "mainserver_2": {ServerStatus.ON: "https://i.postimg.cc/BbL8csTr/mainserver-2-logo.png",
                                                 ServerStatus.OFF: 'https://i.postimg.cc/6pSXSZth/mainserver-2-logo-off.png'}}

    default_server_thumbnail = {ServerStatus.ON: "https://i.postimg.cc/dJgyvGH7/server-symbol.png",
                                ServerStatus.OFF: "https://i.postimg.cc/NfY8CqFL/server-symbol-off.png"}

    server_color_mapping = {"mainserver_1": "ACID_GREEN",
                            "mainserver_2": "AIR_SUPERIORITY_BLUE",
                            "sog_server_1": "SUPER_PINK",
                            "sog_server_2": "UNBLEACHED_SILK",
                            "eventserver": "TEAL_GREEN",
                            "testserver_1": "TROPICAL_VIOLET",
                            "testserver_2": "UCLA_GOLD"}

    default_server_color = "green"
    offline_color = "red"

    # TODO: until here

    cog: "CommunityServerInfoCog" = None
    encoding = 'utf-8'
    lock = DelayedLock(delay=0.001)
    client = None
    status_switch_signal = StatusSwitchSignal()

    schema = ServerSchema()

    def __init__(self, name: str, full_address: str, log_folder: str):
        if self.cog is None:
            raise NeededClassAttributeNotSet('cog', self.__class__.__name__)
        self.name = name
        self._official_name = None
        self.server_address = ServerAddress(full_address)
        self.log_folder = log_folder
        self.log_items = SortedList()
        self.status = ServerStatusDeque()
        self.log_parser = LogParser(self)
        self.battle_metrics_id = self.battle_metrics_mapping.get(self.name.casefold(), None)
        self.battle_metrics_url = '/'.join([self.battlemetrics_base_url, self.battle_metrics_id])
        self.priority = self.server_priority_map.get(self.name.casefold(), 100)
        self._thumbnail = self.server_thumbnail_mapping.get(self.name.casefold(), self.default_server_thumbnail)
        self.on_notification_timeout = {ServerStatus.ON: False, ServerStatus.OFF: False}
        self.last_restart_request_received = None
        self.is_online_message = None

    async def retrieve_is_online_message(self):
        self.is_online_message = await IsOnlineMessage.load(server=self)
        return self.is_online_message

    @property
    def has_access_to_logs(self):
        return self.log_folder is not None

    @property
    def official_name(self):
        if self._official_name is None:
            return self.pretty_name
        return self._official_name

    @classmethod
    async def ensure_client(cls):
        if cls.client is None:
            log.debug("%s client was None", cls.__name__)
            cls.client = AioWebdavClient(**get_nextcloud_options())
            cls.cog.bot.sessions["aiowebdavclient"] = cls.client

    async def get_mod_files(self):
        try:
            if self.log_folder is None or self.current_status is ServerStatus.OFF:
                return ModFileItem(html=None, image=None)

            html_file = await self.log_parser.get_mod_data_html_file()
            image_file = await self.log_parser.get_mod_data_image_file()
            return ModFileItem(html=html_file, image=image_file)
        except TypeError:
            log.critical("TypeError while getting mod files for server %s, server.log_folder= %s, server.current_stats=%s", self.name, self.log_folder, self.current_status)
            return ModFileItem(html=None, image=None)

    async def get_last_restarted_at(self) -> Union[datetime, None]:
        if self.log_folder is None or self.current_status is ServerStatus.OFF:
            return None
        for log_item in self.log_items:
            restart_datetime = await log_item.get_first_logged_correct_time()
            if restart_datetime is not None:
                return restart_datetime
            await asyncio.sleep(0)

    async def get_last_restarted_at_pretty(self) -> str:
        last_restarted = await self.get_last_restarted_at()
        if last_restarted is not None:
            as_date_and_time = last_restarted.strftime(self.cog.bot.std_date_time_format_utc)
            timespan_seconds = (datetime.now(tz=timezone.utc) - last_restarted).total_seconds()
            as_timespan = await asyncio.to_thread(alt_seconds_to_pretty, seconds=timespan_seconds, last_separator=' and ')
            return f"> {as_timespan} ago.\n> `{as_date_and_time}`"

    @cached_property
    def config_name(self) -> str:
        return self.cog.config_name

    @property
    def thumbnail(self):
        return self._thumbnail.get(self.current_status)

    @property
    def color(self):
        if self.current_status is ServerStatus.OFF:
            return self.offline_color
        return self.server_color_mapping.get(self.name.casefold(), self.default_server_color)

    @property
    def previous_status(self):
        return self.status.previous_status

    @property
    def current_status(self):
        return self.status.current_status

    @property
    def notification_time_out(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notification_time_out_seconds', typus=int, direct_fallback=0)

    @property
    def sub_log_folder_name(self) -> str:
        return COGS_CONFIG.retrieve(self.config_name, 'sub_log_folder', typus=str, direct_fallback="Server")

    @property
    def base_log_folder_name(self) -> str:
        return COGS_CONFIG.retrieve(self.config_name, 'base_log_folder', typus=str, direct_fallback="Antistasi_Community_Logs")

    @property
    def log_folder_path(self) -> str:
        return f"{self.base_log_folder_name}/{self.log_folder}/{self.sub_log_folder_name}/"

    @property
    def newest_log_item(self) -> Union[LogFileItem, None]:
        try:
            return self.log_items[0]
        except IndexError as error:
            return None

    @property
    def report_status_change(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, f"{self.name.lower()}_report_status_change", typus=bool, direct_fallback=False)

    @property
    def show_in_server_command(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, f"{self.name.lower()}_show_in_server_command", typus=bool, direct_fallback=True)

    @property
    def is_online_message_enabled(self) -> bool:
        return COGS_CONFIG.retrieve(self.config_name, f"{self.name.lower()}_is_online_message_enabled", typus=bool, direct_fallback=True)

    @property
    def pretty_name(self):
        name_match = self.pretty_name_regex.match(self.name)
        if name_match:
            return ' '.join([group.title() if any(not char.isupper() for char in group) else group for group in name_match.groups() if group])
        return self.name.replace('_', ' ').title()

    async def list_log_items_on_server(self):

        for info_item in await self.client.list(self.log_folder_path, get_info=True):
            if info_item.get('isdir') is False:
                async with self.lock:
                    resource_item = self.client.resource(fix_path(info_item.get('path')))
                    item = LogFileItem(resource_item=resource_item, info=info_item, server_item=self)
                    yield item

    async def gather_log_items(self) -> None:
        if self.log_folder is None:
            return
        new_items = []

        async for remote_log_item in self.list_log_items_on_server():
            new_items.append(remote_log_item)

        self.log_items.clear()
        self.log_items.update(new_items)

        log.info("Gathered %s Log_file_items for Server %s", len(self.log_items), self.name)

    async def update_log_items(self) -> None:
        if self.log_folder is None:
            return
        old_newest_log_item = [self.newest_log_item][0]
        old_items = set(self.log_items)

        await self.gather_log_items()
        for item in set(self.log_items).difference(old_items):
            log.info("New log file %s for server %s", item.name, self.name)
        if old_newest_log_item != self.newest_log_item:
            log.debug("Old newest log item name= %s, created_at= %s | new newest log item name =%s, created_at= %s", old_newest_log_item.name, old_newest_log_item.created, self.newest_log_item.name, self.newest_log_item.created)
            self.log_parser.reset()
            self.newest_log_item.last_real_restart_time = None
            log.critical("Server %s has a new log item, which means he was restarted!", self.name)
            log.debug("invalidating parser cache of %s", self.name)

            asyncio.create_task(self.get_mod_files())
        log.info("Updated log_items for server %s", self.name)

    async def is_online(self) -> ServerStatus:
        try:
            check_data = await self.get_info()
            status = ServerStatus.ON

        except asyncio.exceptions.TimeoutError:
            status = ServerStatus.OFF

        status_has_changed = await self.status.add_new_status(status)
        log.debug(self.log_state_data)
        if self.report_status_change is True and status_has_changed is True:
            log.info("Server %s was switched %s", self, self.current_status.name)
            asyncio.create_task(self._handle_status_change())

        return self.current_status

    async def _handle_status_change(self):
        if self.on_notification_timeout.get(self.current_status) is False:
            log.warning("emiting status_switch_signal for server %s, current_status %s", self.name, self.current_status)
            await self.status_switch_signal.emit(self, self.current_status)
            asyncio.create_task(self._reset_on_notification_timeout(self.current_status))

        else:

            log.debug("Status switch message for Server %s not sent because server is on notification timeout", self.name)

        asyncio.create_task(self.is_online_message.update())

    async def _reset_on_notification_timeout(self, status: ServerStatus):
        self.on_notification_timeout[status] = True
        await asyncio.sleep(self.notification_time_out)
        self.on_notification_timeout[status] = False
        log.debug("finished notification timeout for Server %s and status %s", self.name, str(status))

    async def _retry_get_info(self, try_amount: int = 3, delay: float = 5.0):
        async for try_num in async_range(try_amount):
            try:
                info_data = await a2s.ainfo(self.server_address.query_address, timeout=self.timeout, encoding=self.encoding)
                self._official_name = info_data.server_name
                return info_data
            except asyncio.exceptions.TimeoutError:
                if try_num < (try_amount - 1):
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

    async def get_info(self) -> a2s.SourceInfo:
        info_data = await self._retry_get_info()
        asyncio.create_task(general_db.insert_server_population(self, info_data.player_count))

        return info_data

    async def get_rules(self) -> dict:
        return await a2s.arules(self.server_address.query_address, timeout=self.timeout)

    async def get_players(self) -> list:
        return await a2s.aplayers(self.server_address.query_address, timeout=self.timeout, encoding=self.encoding)

    async def make_server_info_embed(self, with_mods: bool = True):
        if with_mods is True:
            try:
                mod_data = await self.get_mod_files()
            except Exception as error:
                log.error(error)
                return await self.make_server_info_embed(with_mods=False)
        info_data = await self.get_info()
        ping = round(float(info_data.ping), ndigits=3)
        password_needed = "YES 🔐" if info_data.password_protected is True else 'NO 🔓'
        image = self.cog.server_symbol if with_mods is False else mod_data.image
        embed_data = await self.cog.bot.make_generic_embed(title=info_data.server_name,
                                                           thumbnail=image,
                                                           author="armahosts",
                                                           footer="armahosts",
                                                           color="blue",
                                                           fields=[self.cog.bot.field_item(name="Server Address", value=self.server_address.url, inline=True),
                                                                   self.cog.bot.field_item(name="Port", value=self.server_address.port, inline=True),
                                                                   self.cog.bot.field_item(name="Teamspeak", value=f"38.65.5.151  {ZERO_WIDTH}  **OR**  {ZERO_WIDTH}  antistasi.armahosts.com"),
                                                                   self.cog.bot.field_item(name="Game", value=info_data.game, inline=False),
                                                                   self.cog.bot.field_item(name="Players", value=f"{info_data.player_count}/{info_data.max_players}", inline=True),
                                                                   self.cog.bot.field_item(name="Ping", value=ping if ping is not None else "NA", inline=True),
                                                                   self.cog.bot.field_item(name="Map", value=info_data.map_name, inline=True),
                                                                   self.cog.bot.field_item(name="Password", value=f"{password_needed}", inline=True),
                                                                   self.cog.bot.field_item(name='Battlemetrics', value=embed_hyperlink('link to Battlemetrics', self.battle_metrics_url), inline=True)],
                                                           timestamp=self.newest_log_item.modified if self.log_folder is not None else datetime.now(timezone.utc))
        if with_mods is True:
            embed_data['files'].append(mod_data.html)
        return embed_data

    async def dump(self):
        return self.schema.dump(self)

    @property
    def log_state_data(self):
        on_notification_timeout_pretty = {str(key): value for key, value in self.on_notification_timeout.items()}
        text = f"Server {self.name}: 'previous_status'={self.previous_status} <> 'current_status'={self.current_status} <> 'on_notification_timeout'={on_notification_timeout_pretty}"
        return text

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, full_address={self.server_address}, log_folder={self.log_folder})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ServerItem):
            return hash(o) == hash(self)
        return NotImplemented


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
