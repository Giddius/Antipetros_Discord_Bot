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
from webdav3.client import Client as WebdavClient, Urn, OptionNotValid, RemoteResourceNotFound, ResponseErrorCode, MethodNotSupported, NotEnoughSpace, WebDavXmlUtils


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
from inspect import isawaitable
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
            if isawaitable(target):
                await target(server, switched_to)
            else:
                target(server, switched_to)


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
    status_switch_signal = StatusSwitchSignal()

    def __init__(self, name: str, full_address: str, log_base_folder: str) -> None:
        if self.bot is None:
            raise NeededClassAttributeNotSet('bot', self.__class__.__name__)
        if self.config_name is None:
            raise NeededClassAttributeNotSet('config_name', self.__class__.__name__)
        self.name = name
        self.full_address = full_address
        self.log_base_folder = log_base_folder
        self.log_path = f"{self.log_base_folder}/{self.name}"
        self.log_items = []
        self.previous_status = None

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

    async def is_online(self):
        try:
            check_data = await a2s.ainfo(self.query_full_address, timeout=self.timeout)
            status = ServerStatus.ON
        except asyncio.exceptions.TimeoutError:
            status = ServerStatus.OFF

        if self.previous_status is None:
            self.previous_status = status
            return status

        if self.previous_status is not status:
            await self.status_switch_signal.emit(self, status)

    async def get_info(self):
        return await a2s.ainfo(self.query_full_address, encoding=self.encoding)

    async def get_rules(self):
        return await a2s.arules(self.query_full_address)

    async def get_players(self):
        return await a2s.aplayers(self.query_full_address, encoding=self.encoding)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, full_address={self.full_address}, log_base_folder={self.log_base_folder})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
