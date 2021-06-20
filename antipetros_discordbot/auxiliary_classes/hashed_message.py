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
from enum import Enum, Flag, auto, unique
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable, Tuple, Dict, List, Set, Mapping, Optional, TYPE_CHECKING
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord
from discord.ext import commands


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog

from hashlib import blake2b
from functools import cached_property, total_ordering, wraps, partial, lru_cache, singledispatch
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.abstracts.connect_signal import AbstractConnectSignal
from antipetros_discordbot.utility.exceptions import MissingNeededAttributeError, NeededClassAttributeNotSet
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
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


class RemoveHashedMessageSignal(AbstractConnectSignal):

    async def emit(self, hashed_msg: "HashedMessage"):
        await super().emit(hashed_msg)


class HashedMessage:
    bot = None
    config_name = None
    whitespace_regex = re.compile(r'\W')
    storage_timespan = timedelta(minutes=COGS_CONFIG.retrieve(config_name, "remove_double_post_timespan_minutes", typus=int, direct_fallback=20))
    removal_signal = RemoveHashedMessageSignal()

    def __init__(self, channel_id: int, message_id: int, message_hash: str, attachment_hashes: List[str] = None):
        for c_attr_name in ["bot", "config_name"]:
            if getattr(self, c_attr_name) is None:
                raise NeededClassAttributeNotSet(c_attr_name, self.__class__.__name__)
        self.channel_id = channel_id
        self.message_id = message_id
        self.message_hash = message_hash
        self.attachment_hashes = set(attachment_hashes) if attachment_hashes is not None else set()
        self.storage_start_time = datetime.now(tz=timezone.utc)
        self.amount_reposted = 0
        self.removal_task = None

    @property
    def link(self):
        return self.bot.get_message_link(self.channel_id, self.message_id)

    @property
    def remove_at(self) -> datetime:
        return self.storage_start_time + self.storage_timespan

    async def reset_storage_time(self):
        self.storage_start_time = datetime.now(tz=timezone.utc)

    @classmethod
    async def update_store_for_minutes(cls):
        cls.storage_timespan = timedelta(minutes=COGS_CONFIG.retrieve(cls.config_name, "remove_double_post_timespan_minutes", typus=int, direct_fallback=20))

    @classmethod
    async def _clean_content(cls, content: str):
        cleaned_content = discord.utils.remove_markdown(content)
        cleaned_content = cls.whitespace_regex.sub('', cleaned_content)
        return cleaned_content.casefold()

    @classmethod
    async def _hash_content(cls, author_id: int, content: Union[str, bytes]) -> str:
        author_bytes = str(author_id).encode('utf-8', errors='ignore')
        if isinstance(content, str):
            content = content.encode('utf-8', errors='ignore')
        content = author_bytes + content
        content_hash = blake2b(content).hexdigest()
        return content_hash

    @classmethod
    async def from_message(cls, msg: discord.Message):
        author_id = msg.author.id
        channel_id = msg.channel.id
        message_id = msg.id

        message_hash = await cls._hash_content(author_id, await cls._clean_content(msg.content))
        attachment_hashes = [await cls._hash_content(author_id, await attachment.read()) for attachment in msg.attachments] if msg.attachments else None
        hashed_msg_item = cls(channel_id=channel_id, message_id=message_id, message_hash=message_hash, attachment_hashes=attachment_hashes)
        hashed_msg_item.removal_task = asyncio.create_task(hashed_msg_item.check_removal())
        return hashed_msg_item

    async def check_removal(self):
        while datetime.now(tz=timezone.utc) < self.remove_at:
            await asyncio.sleep(60)
        await self.removal_signal.emit(self)

    async def message_exists(self):
        try:
            msg = await self.bot.get_message_directly(self.channel_id, self.message_id)
            log.debug("Message %s exists", msg.id)
            return True
        except discord.errors.NotFound:
            log.debug("Message %s does NOT exists", self.message_id)
            return False

    def __hash__(self):
        _out = hash(self.message_hash)
        for attachment_hash in self.attachment_hashes:
            _out += hash(attachment_hash)
        return _out

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return hash(self) == hash(o)
        return NotImplemented

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
