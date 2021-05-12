"""
[summary]

[extended_summary]
"""

# region [Imports]


import gc

import asyncio
import unicodedata

from enum import Enum, auto, unique
import os
import re

from asyncstdlib import map as async_map
from typing import Union, Callable, TYPE_CHECKING, BinaryIO
from datetime import datetime
from tempfile import TemporaryDirectory
from functools import cached_property, wraps
from contextlib import asynccontextmanager
from dateparser import parse as date_parse

from async_property import async_property, async_cached_property


import gidlogger as glog


from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker, readit, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.regexes import LOG_NAME_DATE_TIME_REGEX, LOG_SPLIT_REGEX, MOD_TABLE_START_REGEX, MOD_TABLE_END_REGEX, MOD_TABLE_LINE_REGEX
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.misc import SIZE_CONV_BY_SHORT_NAME
from antipetros_discordbot.utility.misc import async_list_iterator
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet, NeededConfigValueMissing
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from inspect import isawaitable, iscoroutine
from io import StringIO
import a2s
import aiohttp

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


class LogFileItem:
    size_string_regex = re.compile(r"(?P<number>\d+)\s?(?P<unit>\w+)")

    def __init__(self, resource_item) -> None:
        self.resource_item = resource_item
        self.path = resource_item.urn.path()
        self.name = os.path.basename(self.path)
        self.info = None

    async def get_info(self):
        self.info = await self.resource_item.info()

    @property
    def warning_size_threshold(self):
        limit = COGS_CONFIG.retrieve('antistasi_log_watcher', 'log_file_warning_size_threshold', typus=str, direct_fallback='200mb')
        match_result = self.size_string_regex.search(limit)
        relative_size = int(match_result.group('number'))
        unit = match_result.group('unit').casefold()
        return relative_size * SIZE_CONV_BY_SHORT_NAME.get(unit)

    @property
    def etag(self):
        return self.info.get("etag")

    @property
    def size(self):
        return int(self.info.get("size"))

    @property
    def size_pretty(self):
        return bytes2human(self.size, annotate=True)

    @cached_property
    def created(self):
        return date_parse(self.info.get("created"), settings={'TIMEZONE': 'UTC'}) if self.info.get("created") is not None else self._date_time_from_name()

    @property
    def modified(self):
        return date_parse(self.info.get("modified"), settings={'TIMEZONE': 'UTC'})

    @cached_property
    def created_pretty(self):
        return self.created.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def modified_pretty(self):
        return self.modified.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_over_threshold(self):
        if self.size >= self.warning_size_threshold:
            return True
        return False

    def _date_time_from_name(self):
        matched_data = LOG_NAME_DATE_TIME_REGEX.search(os.path.basename(self.path))
        if matched_data:
            date_time_string = f"{matched_data.group('year')}-{matched_data.group('month')}-{matched_data.group('day')} {matched_data.group('hour')}:{matched_data.group('minute')}:{matched_data.group('second')}"
            date_time = datetime.strptime(date_time_string, "%Y-%m-%d %H:%M:%S")
            return date_time
        else:
            raise RuntimeError(f'unable to find date_time_string in {os.path.basename(self.path)}')

    async def content(self, buffer):
        return await self.resource_item.client.download_to(self.path, buffer)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with path '{self.path}'"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" + ', '.join(map(str, [self.created_pretty, self.etag, self.modified_pretty, self.name, self.path, self.size, self.size_pretty])) + ')'


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


class StatusSwitchSignal:

    def __init__(self) -> None:
        self.targets = []

    def connect(self, target: Callable):
        self.targets.append(target)

    async def emit(self, server: "ServerItem", switched_to: ServerStatus):
        for target in self.targets:

            await target(server, switched_to)


class ServerItem:
    timeout = 1
    battle_metrics_mapping = {'mainserver_1': "https://www.battlemetrics.com/servers/arma3/10560386",
                              'mainserver_2': "https://www.battlemetrics.com/servers/arma3/10561000",
                              'testserver_1': "https://www.battlemetrics.com/servers/arma3/4789978",
                              'testserver_2': "https://www.battlemetrics.com/servers/arma3/9851037",
                              'eventserver': "https://www.battlemetrics.com/servers/arma3/9552734"}
    bot = None
    config_name = None
    encoding = 'utf-8'
    delta_query_port = 1

    def __init__(self, name: str, full_address: str, log_folder: str) -> None:
        if self.bot is None:
            raise NeededClassAttributeNotSet('bot', self.__class__.__name__)
        if self.config_name is None:
            raise NeededClassAttributeNotSet('config_name', self.__class__.__name__)
        self.name = name
        self.full_address = full_address
        self.log_folder = log_folder
        self.log_items = []
        self.previous_status = None
        self.status_switch_signal = StatusSwitchSignal()

    @property
    def client(self):
        return self.bot.webdav_client

    @property
    def address(self):
        return self.full_address.split(':')[0]

    @property
    def port(self):
        return int(self.full_address.split(':')[-1])

    @property
    def query_port(self):
        return self.port + self.delta_query_port

    @property
    def query_full_address(self):
        return (self.address, self.query_port)

    @property
    def sub_log_folder_name(self):
        return COGS_CONFIG.retrieve(self.config_name, 'sub_log_folder', typus=str, direct_fallback="Server")

    @property
    def base_log_folder_name(self):
        return COGS_CONFIG.retrieve(self.config_name, 'base_log_folder', typus=str, direct_fallback="Antistasi_Community_Logs")

    @property
    def log_folder_path(self):
        return f"{self.base_log_folder_name}/{self.log_folder}/{self.sub_log_folder_name}/"

    async def gather_log_items(self):
        async for log_file_resource in self.list():
            item = LogFileItem(log_file_resource)
            await item.get_info()
            self.log_items.append(item)

        self.log_items = sorted(self.log_items, key=lambda x: x.modified, reverse=True)

        log.info("Gathered %s Log_file_items for Server %s", len(self.log_items), self.name)

    async def is_online(self):
        try:
            check_data = await a2s.ainfo(self.query_full_address, timeout=self.timeout)
            status = ServerStatus.ON
        except asyncio.exceptions.TimeoutError:
            status = ServerStatus.OFF
        log.info("Server %s is %s", self.name, status.name)

        if self.previous_status is not None and self.previous_status is not status:
            await self.status_switch_signal.emit(self, status)
        self.previous_status = status
        return status

    async def get_info(self):
        return await a2s.ainfo(self.query_full_address, encoding=self.encoding)

    async def get_rules(self):
        return await a2s.arules(self.query_full_address)

    async def get_players(self):
        return await a2s.aplayers(self.query_full_address, encoding=self.encoding)

    async def list(self):
        for file_name in await self.client.list(self.log_folder_path):
            if not file_name.endswith('/'):
                item = self.client.resource(f"{self.log_folder_path}/{file_name}")
                yield item
                await asyncio.sleep(0)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, full_address={self.full_address}, log_base_folder={self.log_base_folder})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
