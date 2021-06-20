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
import re
from asyncstdlib import map as async_map
from typing import TYPE_CHECKING
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
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.regexes import LOG_SPLIT_REGEX, MOD_TABLE_END_REGEX, MOD_TABLE_LINE_REGEX, MOD_TABLE_START_REGEX
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.misc import SIZE_CONV_BY_SHORT_NAME
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from jinja2 import Environment, FileSystemLoader, BaseLoader
from io import BytesIO
import a2s
from weasyprint import HTML
import aiohttp
from aiodav.exceptions import NoConnection
from sortedcontainers import SortedDict, SortedList
from marshmallow import Schema, fields
from hashlib import shake_256
if TYPE_CHECKING:
    from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog
from zipfile import ZipFile, ZIP_LZMA
from antipetros_discordbot.abstracts.connect_signal import AbstractConnectSignal
from pyparsing import (Word, alphanums, punc8bit, alphas, Literal, Optional, OneOrMore, oneOf, Group, nums, nestedExpr, delimitedList,
                       dblQuotedString, quotedString, Forward, Suppress, SkipTo, ZeroOrMore, Combine, Regex, Keyword, CaselessLiteral,
                       restOfLine, ParserElement, countedArray, CharsNotIn, cStyleComment, commaSeparatedList, cppStyleComment, LineEnd,
                       LineStart, NotAny, removeQuotes, nestedExpr, CaselessKeyword, CaselessLiteral, FollowedBy)

import pyparsing as pp

from antipetros_discordbot.utility.sqldata_storager import general_db
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

    def __init__(self):
        super().__init__(maxlen=2)
        self.append(None)
        self.append(None)

    @property
    def current_status(self) -> ServerStatus:
        return self[1]

    @property
    def previous_status(self) -> ServerStatus:
        return self[0]

    def add_new_status(self, status: ServerStatus):
        self.append(status)


@unique
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


class UpdateIsOnlineMessageSignal(AbstractConnectSignal):

    async def emit(self, server: "ServerItem"):
        return await super().emit(server)


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

    def __init__(self, server_item: "ServerItem") -> None:
        self._mod_lookup_data = None
        self.server = server_item
        self.current_log_item = None
        self.current_byte_position = 0
        self.jinja_env = Environment(loader=BaseLoader, enable_async=True)
        self._parsed_data = None

    @property
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
            async for chunk in await self.server.newest_log_item.content_iter():
                current_content_bytes.append(chunk)
            current_content = b''.join(current_content_bytes).decode('utf-8', errors='ignore')
            split_match = LOG_SPLIT_REGEX.search(current_content)
            if split_match:
                pre_content = current_content[:split_match.end()]
                cleaned_lower = MOD_TABLE_START_REGEX.split(pre_content)[-1]
                mod_table = MOD_TABLE_END_REGEX.split(cleaned_lower)[0]
                for line in mod_table.splitlines():
                    if line != '':
                        line_match = MOD_TABLE_LINE_REGEX.search(line)
                        _out.append({key: value.strip() for key, value in line_match.groupdict().items()})
                    await asyncio.sleep(0)

                items = [item.get('mod_dir') for item in _out if item.get('official') == 'false' and item.get("mod_name") not in {"@members", "@TaskForceEnforcer", "@utility"}]
                self._parsed_data = sorted(items)
        return self._parsed_data

    async def _render_mod_data(self) -> str:
        mod_data = await self._parse_mod_data()
        if mod_data is None:
            await asyncio.sleep(30)
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
        weasy_html = HTML(string=html_string)
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

    @property
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


@total_ordering
class LogFileItem:
    config_name = None
    size_string_regex = re.compile(r"(?P<number>\d+)\s?(?P<unit>\w+)")
    log_name_regex = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")
    schema = LogFileSchema()
    lock = asyncio.Lock()
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

    async def collect_info(self) -> None:
        async with self.lock:
            self.info = await self.resource_item.info()

    async def update(self):
        return NotImplemented

    @classmethod
    @property
    def warning_size_threshold(cls) -> int:
        limit = COGS_CONFIG.retrieve(cls.config_name, 'log_file_warning_size_threshold', typus=str, direct_fallback='200mb')
        match_result = cls.size_string_regex.search(limit)
        relative_size = int(match_result.group('number'))
        unit = match_result.group('unit').casefold()
        return relative_size * SIZE_CONV_BY_SHORT_NAME.get(unit)

    @property
    def etag(self) -> str:
        return self.info.get("etag").strip('"')

    @property
    def modified(self) -> datetime:
        return date_parse(self.info.get("modified"), settings={'TIMEZONE': 'UTC'})

    @property
    def size(self) -> int:
        return int(self.info.get("size"))

    @property
    def size_pretty(self) -> str:
        return bytes2human(self.size, annotate=True)

    @cached_property
    def created_pretty(self) -> str:
        return self.created.strftime(self.time_pretty_format)

    @property
    def modified_pretty(self) -> str:
        return self.modified.strftime(self.time_pretty_format)

    @property
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

    async def content_embed(self):
        await self.collect_info()

        with BytesIO() as bytefile:
            name = self.name.split('.')[0] + '.zip'
            if self.size > self.server_item.cog.bot.filesize_limit:
                with ZipFile(bytefile, 'w', ZIP_LZMA) as zippy:
                    content_bytes = b''
                    async with self.lock:
                        async for chunk in await self.content_iter():
                            content_bytes += chunk
                        zippy.writestr(self.name, content_bytes.decode('utf-8', 'ignore'))
            else:
                name = self.name
                async with self.lock:
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

    @property
    def delta_query_port(self) -> int:
        return BASE_CONFIG.retrieve("arma", "delta_query_port", typus=int, direct_fallback=1)

    @property
    def query_port(self):
        return self.port + self.delta_query_port

    @property
    def query_address(self):
        return (self.url, self.query_port)

    def __str__(self) -> str:
        return f"{self.url}:{self.port}:{self.query_port}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.full_address})"


class ServerItem:
    pretty_name_regex = re.compile(r"(?P<name>[a-z]+)\_?(?P<server>server)\_?(?P<number>\d)?", re.IGNORECASE)
    timeout = 3.0
    battle_metrics_mapping = {'mainserver_1': "https://www.battlemetrics.com/servers/arma3/10560386",
                              'mainserver_2': "https://www.battlemetrics.com/servers/arma3/10561000",
                              'testserver_1': "https://www.battlemetrics.com/servers/arma3/4789978",
                              'testserver_2': "https://www.battlemetrics.com/servers/arma3/9851037",
                              'eventserver': "https://www.battlemetrics.com/servers/arma3/9552734",
                              'sog_server_1': "https://www.battlemetrics.com/servers/arma3/11406516",
                              'sog_server_2': "https://www.battlemetrics.com/servers/arma3/11406517"}

    server_priority_map = {"mainserver_1": 1,
                           "mainserver_2": 2,
                           "sog_server_1": 3,
                           "sog_server_2": 4,
                           "eventserver": 5,
                           "testserver_1": 6,
                           "testserver_2": 7}

    cog: "AntiPetrosBaseCog" = None
    encoding = 'utf-8'
    limit_lock = AioLock()

    client = None
    status_switch_signal = StatusSwitchSignal()
    update_is_online_message_signal = UpdateIsOnlineMessageSignal()
    schema = ServerSchema()

    def __init__(self, name: str, full_address: str, log_folder: str):
        if self.cog is None:
            raise NeededClassAttributeNotSet('cog', self.__class__.__name__)
        self.name = name
        self.official_name = None
        self.server_address = ServerAddress(full_address)
        self.log_folder = log_folder
        self.log_items = SortedList()
        self.status = ServerStatusDeque()
        self.log_parser = LogParser(self)
        self.battle_metrics_url = self.battle_metrics_mapping.get(self.name.casefold(), None)
        self.priority = self.server_priority_map.get(self.name.casefold(), 0)
        self.on_notification_timeout = {ServerStatus.ON: False, ServerStatus.OFF: False}

    @classmethod
    async def ensure_client(cls):
        if cls.client is None:
            log.debug("%s client was None", cls.__name__)
            cls.client = AioWebdavClient(**get_nextcloud_options())
            cls.cog.bot.sessions["aiowebdavclient"] = cls.client

    async def get_mod_files(self):
        html_file = await self.log_parser.get_mod_data_html_file()
        image_file = await self.log_parser.get_mod_data_image_file()
        return ModFileItem(html=html_file, image=image_file)

    @cached_property
    def config_name(self) -> str:
        return self.cog.config_name

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
    def newest_log_item(self) -> LogFileItem:
        return self.log_items[0]

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
        async with self.limit_lock:
            for info_item in await self.client.list(self.log_folder_path, get_info=True):
                if info_item.get('isdir') is False:
                    resource_item = self.client.resource(fix_path(info_item.get('path')))
                    item = LogFileItem(resource_item=resource_item, info=info_item, server_item=self)
                    yield item
                    await asyncio.sleep(0)

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
        old_newest_log_item = deepcopy(self.newest_log_item)
        old_items = set(self.log_items)
        await self.gather_log_items()
        for item in set(self.log_items).difference(old_items):
            log.info("New log file %s for server %s", item.name, self.name)
        if old_newest_log_item is not self.newest_log_item:
            self.log_parser.reset()
            log.debug("invalidating parser cache of %s", self.name)
            if self.log_folder is not None and self.previous_status is ServerStatus.ON:
                asyncio.create_task(self.get_mod_files())
        log.info("Updated log_items for server %s", self.name)

    async def is_online(self) -> ServerStatus:
        log.debug("for Server %s before checking status, previous status is %s", self, str(self.current_status))
        try:
            check_data = await self.get_info()
            self.status.add_new_status(ServerStatus.ON)
            self.official_name = check_data.server_name
        except asyncio.exceptions.TimeoutError:
            self.status.add_new_status(ServerStatus.OFF)
        log.info("Server %s is %s", self.name, self.current_status.name)

        if all([self.report_status_change is True,
                self.previous_status not in {None, self.current_status}]):
            log.debug("Server Status %s is on timeout %s", str(self.current_status), self.on_notification_timeout.get(self.current_status))
            if self.on_notification_timeout.get(self.current_status) is False:
                log.debug("Server %s status notification for status %s is not on timeout", self, str(self.current_status))
                await self.status_switch_signal.emit(self, self.current_status)

                asyncio.create_task(self._reset_on_notification_timeout(self.current_status))
            else:
                log.debug("Status switch message for Server %s not sent because server is on notification timeout", self.name)

            if self.is_online_message_enabled is True:
                await self.update_is_online_message_signal.emit(self)

        return self.current_status

    async def _reset_on_notification_timeout(self, status: ServerStatus):
        self.on_notification_timeout[status] = True
        await asyncio.sleep(self.notification_time_out)
        self.on_notification_timeout[status] = False
        log.debug("finished notification timeout for Server %s and status %s", self.name, str(status))

    async def get_info(self) -> a2s.SourceInfo:
        info_data = await a2s.ainfo(self.server_address.query_address, encoding=self.encoding)
        asyncio.create_task(general_db.insert_server_population(self, info_data.player_count))
        return info_data

    async def get_rules(self) -> dict:
        return await a2s.arules(self.server_address.query_address)

    async def get_players(self) -> list:
        return await a2s.aplayers(self.server_address.query_address, encoding=self.encoding)

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
