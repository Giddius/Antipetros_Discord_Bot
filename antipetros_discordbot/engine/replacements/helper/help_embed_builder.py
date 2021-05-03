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
from abc import ABC, abstractmethod, ABCMeta
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from time import time, sleep, monotonic_ns, time_ns
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable, TYPE_CHECKING, List, Dict, Any, Optional, Tuple, Set, Awaitable, get_type_hints, get_args, Mapping, Awaitable
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, singledispatchmethod
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserDict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord


from jinja2 import BaseLoader, Environment

from natsort import natsorted

from fuzzywuzzy import fuzz, process
from discord.ext import commands, tasks, flags, ipc

import gidlogger as glog

from antipetros_discordbot.auxiliary_classes.all_item import AllItem
from antipetros_discordbot.utility.exceptions import ParameterError
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writeit
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink, make_box
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus, ExtraHelpParameter, HelpCategory
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.general_decorator import is_refresh_task, universal_log_profiler, handler_method
from antipetros_discordbot.utility.gidtools_functions import loadjson, readit
from async_property import async_property
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink, make_box
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, SPECIAL_SPACE, ListMarker, Seperators
import inflect
import inspect
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

    from antipetros_discordbot.engine.replacements.helper import CommandCategory


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
inflect_engine = inflect.engine()
# endregion[Constants]


class StringKeyDict(UserDict):
    def __init__(self, in_dict: dict = None) -> None:
        super().__init__(__dict={str(key): value for key, value in in_dict.items()} if in_dict is not None else in_dict)

    def __setitem__(self, key, item):
        super().__setitem__(key=str(key), item=item)

    def __getitem__(self, key):
        return super().__getitem__(key=str(key))

    def __delitem__(self, key):
        super().__delitem__(key=str(key))

    def __contains__(self, key):
        return super().__contains__(key=str(key))

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[str(key)] = value
        return d


class AbstractProvider(ABC):
    field_item = EmbedFieldItem

    def __init__(self, in_builder: "HelpCommandEmbedBuilder"):
        self.bot = in_builder.bot
        self.command = in_builder.command
        self.member = in_builder.member

    @abstractmethod
    async def __call__(self):
        ...

    @classmethod
    @property
    @abstractmethod
    def provides(cls):
        ...

    @property
    def is_group(self):
        return isinstance(self.command, commands.Group)

    @property
    def is_sub_command(self):
        return self.command.parent is not None

    @property
    def member_can_invoke(self):
        member_roles = set([AllItem()] + [role for role in self.member.roles])
        if set(self.command.allowed_roles).isdisjoint(member_roles) is False:
            return True
        if self.member in self.command.allowed_members or AllItem() in self.command.allowed_members:
            return True
        return False


class AbstractFieldProvider(AbstractProvider):
    provides = 'fields'

    def __init__(self, in_builder: "HelpCommandEmbedBuilder"):
        super().__init__(in_builder)
        self.all_handler = None
        self.field_name_handler = self._no_handling
        self._set_handler_attribute()

    def _set_handler_attribute(self):
        self.all_handler = {}
        for method_name, method_object in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method_object, 'is_handler') and method_object.is_handler is True:
                self.all_handler[method_object.handled_attr] = partial(method_object, attr_name=method_object.handled_attr)

    @ classmethod
    @ property
    def bool_symbol_map(cls) -> Dict[bool, str]:
        return NotImplemented

    async def _no_handling(self, in_data):
        return in_data

    def add_handler(self, new_handler: Callable):
        if not inspect.iscoroutinefunction(new_handler):
            raise TypeError('new_handler needs to be a coroutine')
        if not hasattr(new_handler, 'is_handler'):
            new_handler = handler_method(new_handler)
            self.all_handler[new_handler.handled_attr] = partial(new_handler, new_handler.handled_attr)


class DefaultTitleProvider(AbstractProvider):
    provides = 'title'

    async def __call__(self):
        if self.is_sub_command:
            return f"{self.command.parent.name} {self.command.name}"

        return self.command.name


class DefaultDescriptionProvider(AbstractProvider):
    provides = 'description'

    async def __call__(self):
        description = self.command.description
        if self.member_can_invoke is False:
            description = f"__** You do not have the necesary roles to actually invoke this command**__\n{ZERO_WIDTH}\n" + description
        return description


class DefaulThumbnailProvider(AbstractProvider):
    provides = "thumbnail"

    async def __call__(self):
        return None


class DefaulImageProvider(AbstractProvider):
    provides = "image"

    async def __call__(self):
        return None


class DefaultAuthorProvider(AbstractProvider):
    provides = "author"

    async def __call__(self):
        return {'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}


class DefaultfooterProvider(AbstractProvider):
    provides = 'footer'

    async def __call__(self):
        return None


class DefaulURLProvider(AbstractProvider):
    provides = 'url'

    async def __call__(self):
        return self.command.github_wiki_link


class DefaultFieldsProvider(AbstractFieldProvider):
    bool_symbol_map = {True: '✅',
                       False: '❎'}

    async def __call__(self):
        fields = []
        for handler_attr, handler_func in self.all_handler.items():
            if hasattr(self.command, handler_attr):
                new_item = await handler_func()
                if new_item is not None:
                    fields.append(new_item)
        return fields

    @ property
    def visible_channels(self):
        _out = []
        for channel in self.command.allowed_channels:
            if channel.name.casefold() == 'all':
                _out.append(channel)

            else:
                channel_member_permissions = channel.permissions_for(self.member)
                if channel_member_permissions.administrator is True or channel_member_permissions.read_messages is True:
                    _out.append(channel)
        return _out

    @ handler_method
    async def _handle_usage(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = CodeBlock(getattr(self.command, attr_name), 'css')
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_aliases(self, attr_name):
        name = await self.field_name_handler(attr_name)
        items = [f"`{alias}`" for alias in getattr(self.command, attr_name)]
        value = ListMarker.make_list(items)
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_allowed_channels(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = ListMarker.make_column_list([channel.mention for channel in self.visible_channels], ListMarker.star)
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_allowed_roles(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = '\n'.join(role.mention for role in getattr(self.command, attr_name))
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_allowed_in_dm(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = self.bool_symbol_map.get(getattr(self.command, attr_name))
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_github_link(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = embed_hyperlink('link 🔗', getattr(self.command, attr_name))
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_github_wiki_link(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = embed_hyperlink('link 🔗', getattr(self.command, attr_name))
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_extra_info(self, attr_name):
        name = await self.field_name_handler(attr_name)
        attr_value = getattr(self.command, attr_name)
        if attr_value is None:
            return None
        value = f"`{attr_value}`"
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @handler_method
    async def _handle_example(self, attr_name):
        name = await self.field_name_handler(attr_name)
        value = CodeBlock(getattr(self.command, attr_name), 'css')
        inline = False
        return self.field_item(name=name, value=value, inline=inline)


class DefaultColorProvider(AbstractProvider):
    provides = 'color'

    async def __call__(self):
        return 'GIDDIS_FAVOURITE'


class DefaultTimestampProvider(AbstractProvider):
    provides = 'timestamp'

    async def __call__(self):
        return datetime.now(tz=timezone.utc)


class HelpCommandEmbedBuilder:
    field_item = EmbedFieldItem

    default_title_provider = DefaultTitleProvider
    default_description_provider = DefaultDescriptionProvider
    default_thumbnail_provider = DefaulThumbnailProvider
    default_image_provider = DefaulImageProvider
    default_author_provider = DefaultAuthorProvider
    default_footer_provider = DefaultfooterProvider
    default_fields_provider = DefaultFieldsProvider
    default_url_provider = DefaulURLProvider
    default_color_provider = DefaultColorProvider
    default_Timestamp_provider = DefaultTimestampProvider

    def __init__(self, bot: "AntiPetrosBot", invoking_person: Union[discord.Member, discord.User], command: Union["AntiPetrosBaseCommand", "AntiPetrosBaseGroup", "AntiPetrosFlagCommand"]):
        self.bot = bot
        self.command = command
        self.member = self.bot.members_dict.get(invoking_person.id) if isinstance(invoking_person, discord.User) else invoking_person

        self.title_provider = self.default_title_provider(self)
        self.description_provider = self.default_description_provider(self)
        self.thumbnail_provider = self.default_thumbnail_provider(self)
        self.image_provider = self.default_image_provider(self)
        self.author_provider = self.default_author_provider(self)
        self.footer_provider = self.default_footer_provider(self)
        self.fields_provider = self.default_fields_provider(self)
        self.url_provider = self.default_url_provider(self)
        self.color_provider = self.default_color_provider(self)
        self.timestamp_provider = self.default_Timestamp_provider(self)

    def set_provider(self, provider: AbstractProvider):
        setattr(self, provider.provides + '_provider', provider(self))

    async def to_embed(self):
        embed_data = await self.bot.make_generic_embed(title=await self.title_provider(),
                                                       description=await self.description_provider(),
                                                       thumbnail=await self.thumbnail_provider(),
                                                       image=await self.image_provider(),
                                                       author=await self.author_provider(),
                                                       fields=await self.fields_provider(),
                                                       url=await self.url_provider(),
                                                       color=await self.color_provider(),
                                                       timestamp=await self.timestamp_provider())
        return embed_data

# region[Main_Exec]


if __name__ == '__main__':
    pass
# endregion[Main_Exec]
