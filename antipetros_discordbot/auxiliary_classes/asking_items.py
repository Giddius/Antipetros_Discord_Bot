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
from typing import Union, Callable, Iterable, Optional, TYPE_CHECKING
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
import collections.abc

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI, letter_to_emoji, CANCEL_EMOJI
from antipetros_discordbot.utility.exceptions import MissingNeededAttributeError, NeededClassAttributeNotSet
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import better_shorten, async_better_shorten, alternative_better_shorten
if TYPE_CHECKING:
    pass

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

# endregion[Constants]


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]


class AskAnswer(Enum):
    ACCEPTED = auto()
    DECLINED = auto()
    CANCELED = auto()
    NOANSWER = auto()
    FINISHED = auto()


class AskingTypus(Enum):
    CONFIRMATION = auto()
    SELECTION = auto()
    INPUT = auto()
    FILE = auto()

    @classmethod
    def get_typus(cls, ask_class):
        query_name = ask_class.__name__.upper().removeprefix('ASK')
        for item in cls:
            if item.name == query_name:
                return item
        return NotImplemented


class AskSelectionOption:

    def __init__(self, item, emoji: Optional[Union[str, discord.Emoji]] = None, name: Optional[str] = None, description: Optional[Union[str, Callable]] = None):
        self.item = item
        self.emoji = emoji
        self._description = description
        self._name = name

    @cached_property
    def name(self):
        if self._name is not None:
            return self._name
        if isinstance(self.item, str):
            return self.item
        if hasattr(self.item, "name"):
            return self.item.name

        return str(self.item)

    @cached_property
    def description(self):
        if self._description is None:
            return ZERO_WIDTH

        if isinstance(self._description, str):
            return self._description

        if callable(self._description):
            try:
                return self._description(self.item)
            except Exception as error:
                log.debug("error in retrieving %s description for %s, error: %s", self.__class__.__name__, self.name, error)
                return ZERO_WIDTH


class AskSelectionOptionsMapping(collections.abc.Mapping):

    def __init__(self, default_emojis: Optional[list[Union[str, discord.Emoji]]] = None):
        self.options = {}
        self.default_emoji_list = list(default_emojis) if default_emojis is not None else []
        self.default_emoji_list += ALPHABET_EMOJIS.copy()

    def add_option(self, option: AskSelectionOption):

        if isinstance(option.emoji, int) and 0 < option.emoji < 11:
            key = NUMERIC_EMOJIS[option.emoji - 1]

        elif isinstance(option.emoji, str) and len(option.emoji) == 1 and option.emoji[0].isalpha():
            key = letter_to_emoji(option.emoji[0])

        else:
            key = option.emoji

        if key is None:
            key = self.default_emoji_list.pop(0)
        option.emoji = key
        self.options[str(key)] = option

    def add_many_options(self, options: Iterable[AskSelectionOption]):
        for option in options:
            self.add_option(option)

    def get(self, key, default=None):
        return self.options.get(str(key), default)

    def __iter__(self):
        return iter(self.options)

    def __contains__(self, o: object) -> bool:
        if isinstance(o, (str, discord.Emoji, discord.PartialEmoji)):
            return str(o) in self.options
        return NotImplemented

    def __len__(self):
        return len(self.options)

    def __getitem__(self, key):
        return self.options[str(key)]

    def __setitem__(self, key, value):
        self.options[str(key)] = value

    async def asyncio_items(self):
        for key, value in self.options.items():
            yield key, value
            await asyncio.sleep(0)

    def values(self):
        return self.options.values()

    def items(self):
        return self.options.items()

    def get_result(self, key):
        return self.options.get(str(key)).item

    async def to_fields(self):
        fields = []
        async for key, option in self.asyncio_items():
            option_description = option.description
            fields.append(await asyncio.sleep(0, EmbedFieldItem(name=f"***Press {key} for `{option.name}`***", value=f"{option_description}", inline=False)))
        return fields


class AbstractUserAsking(ABC):
    ACCEPTED = AskAnswer.ACCEPTED
    DECLINED = AskAnswer.DECLINED
    CANCELED = AskAnswer.CANCELED
    NOANSWER = AskAnswer.NOANSWER
    FINISHED = AskAnswer.FINISHED
    cancel_emoji = CANCEL_EMOJI
    cancel_phrase = "!CANCEL!"
    none_phrase = "!NONE!"
    confirm_emoji = CHECK_MARK_BUTTON_EMOJI
    decline_emoji = CROSS_MARK_BUTTON_EMOJI
    error_answers = {AskAnswer.CANCELED, AskAnswer.NOANSWER}

    bot = None
    mandatoy_attributes = ['bot']

    def __init__(self, author: Union[int, discord.Member, discord.User], channel: Union[int, discord.DMChannel, discord.TextChannel], timeout: int = 300, delete_question: bool = False) -> None:
        for c_attr_name in self.mandatoy_attributes:
            if getattr(self, c_attr_name) is None:
                raise NeededClassAttributeNotSet(c_attr_name, self.__class__.__name__)
        self.timeout = timeout
        self.channel = self._ensure_channel(channel)
        self.author = self._ensure_author(author)

        self.delete_question = delete_question
        self.title = None
        self.description = ZERO_WIDTH
        self.thumbnail = None
        self.fields = []
        self.ask_message = None
        self.ask_embed_data = None
        self.end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=timeout)

    def _ensure_author(self, author: Union[int, discord.Member, discord.User]) -> Union[discord.Member, discord.User]:
        if isinstance(self.channel, discord.DMChannel):
            return self.channel.recipient

        if isinstance(author, discord.Member):
            return author

        if isinstance(author, int):
            return self.bot.get_antistasi_member(author)

    def _ensure_channel(self, channel: Union[int, discord.TextChannel, discord.DMChannel]) -> Union[discord.TextChannel, discord.DMChannel]:
        if isinstance(channel, (discord.TextChannel, discord.DMChannel)):
            return channel
        return self.bot.channel_from_id(channel)

    @classmethod
    @property
    @abstractmethod
    def typus(cls) -> AskingTypus:
        ...

    @classmethod
    @property
    @abstractmethod
    def wait_for_event(cls):
        ...

    @abstractmethod
    async def transform_answer(self, answer):
        ...

    @abstractmethod
    async def transform_ask_message(self):
        ...

    async def make_fields(self):
        return [self.bot.field_item(name="Time to answer", value=alt_seconds_to_pretty(int(self.timeout)), inline=False),
                self.bot.field_item(name=f"{self.cancel_emoji} to Cancel", value=ZERO_WIDTH, inline=False)]

    async def make_ask_embed(self, **kwargs):
        return await self.bot.make_asking_embed(typus=self.typus, timeout=self.timeout, description=self.description, fields=await self.make_fields(), title=self.title, **kwargs)

    async def on_timeout(self):
        return self.NOANSWER

    @abstractmethod
    def check_if_answer(self):
        ...

    async def update_ask_embed_data(self):
        pass

    async def _ask_mechanism(self):
        timeout = (self.end_time - datetime.now(tz=timezone.utc)).total_seconds()
        await self.update_ask_embed_data()
        try:
            return await self.bot.wait_for(event=self.wait_for_event, timeout=timeout, check=self.check_if_answer)
        except asyncio.TimeoutError:
            return await self.on_timeout()

    async def ask(self, **kwargs):
        self.ask_embed_data = await self.make_ask_embed(**kwargs)
        self.ask_message = await self.channel.send(**self.ask_embed_data)
        await self.transform_ask_message()
        answer = await self._ask_mechanism()

        await self.after_ask()
        return await self.transform_answer(answer)

    async def after_ask(self):
        try:
            if self.delete_question is True:
                await self.ask_message.delete()
        except discord.errors.Forbidden:
            log.debug("unable to delete message, because it is Forbidden")

        try:
            if self.channel.type is discord.ChannelType.text:
                await self.ask_message.clear_reactions()
        except discord.errors.Forbidden:
            log.debug("unable to delete reactions, because it is Forbidden")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


class AskConfirmation(AbstractUserAsking):
    wait_for_event = 'raw_reaction_add'
    typus = AskingTypus.CONFIRMATION

    def __init__(self, author: Union[int, discord.Member, discord.User], channel: Union[int, discord.DMChannel, discord.TextChannel], timeout: int = 300, delete_question: bool = False) -> None:
        super().__init__(timeout=timeout, author=author, channel=channel, delete_question=delete_question)

    @cached_property
    def answer_table(self):
        return {self.cancel_emoji: self.CANCELED,
                self.confirm_emoji: self.ACCEPTED,
                self.decline_emoji: self.DECLINED}

    async def transform_answer(self, answer):

        answer_emoji = str(answer.emoji)
        return self.answer_table.get(answer_emoji)

    def check_if_answer(self, payload: discord.RawReactionActionEvent):
        checks = [payload.user_id == self.author.id,
                  payload.channel_id == self.channel.id,
                  str(payload.emoji) in self.answer_table]

        return all(checks)

    async def transform_ask_message(self):
        for emoji in self.answer_table:
            await self.ask_message.add_reaction(emoji)


class AskInput(AbstractUserAsking):
    wait_for_event = 'message'
    typus = AskingTypus.INPUT

    def __init__(self, author: Union[int, discord.Member, discord.User], channel: Union[int, discord.DMChannel, discord.TextChannel], timeout: int = 300, delete_question: bool = False, validator: Callable = None) -> None:
        super().__init__(timeout=timeout, author=author, channel=channel, delete_question=delete_question)
        self.validator = self.default_validator if validator is None else validator

    async def make_fields(self):
        fields = await super().make_fields()
        fields = [fields[0], self.bot.field_item(name=f"Type {self.cancel_phrase} to cancel", value=ZERO_WIDTH, inline=False)]
        return fields

    def default_validator(self, content):
        return content != ""

    async def transform_answer(self, answer):
        if answer.content == self.cancel_phrase:
            return self.CANCELED
        return answer.content

    def check_if_answer(self, message: discord.Message):
        checks = [message.author.id == self.author.id,
                  message.channel.id == self.channel.id]

        return all(checks) and self.validator(message.content) is True

    async def transform_ask_message(self):
        pass


class AskFile(AbstractUserAsking):
    typus = AskingTypus.FILE
    wait_for_event = 'message'
    allowed_file_types = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'tiff', 'tga'}

    def __init__(self, author: Union[int, discord.Member, discord.User], channel: Union[int, discord.DMChannel, discord.TextChannel], timeout: int = 300, delete_question: bool = False, file_validator: Callable = None) -> None:
        super().__init__(author=author, channel=channel, timeout=timeout, delete_question=delete_question)
        self.file_validator = self.default_file_validator if file_validator is None else file_validator

    async def make_fields(self):
        fields = await super().make_fields()
        fields = [fields[0], self.bot.field_item(name=f"Type {self.cancel_phrase} to cancel", value=ZERO_WIDTH, inline=False)]
        fields.append(self.bot.field_item(name="If you do not want to Attach a file, type `!NONE!", value=ZERO_WIDTH, inline=False))
        fields.append(self.bot.field_item(name="allowed File Types", value=','.join(f"`{ftype}`" for ftype in self.allowed_file_types), inline=False))
        return fields

    async def transform_answer(self, answer):
        if answer.content == self.cancel_phrase:
            return self.CANCELED
        if answer.content == self.none_phrase and answer.attachments == []:
            return []

        return answer.attachments

    async def on_timeout(self):
        return self.NOANSWER

    def default_file_validator(self, attachments):
        if attachments is None or attachments == []:
            return True

        return all(attachment.filename.casefold().split('.')[-1] in self.allowed_file_types for attachment in attachments)

    def check_if_answer(self, message: discord.Message):
        checks = [message.author.id == self.author.id,
                  message.channel.id == self.channel.id]

        if all(checks):
            if message.content not in {self.none_phrase, self.cancel_phrase} and not message.attachments:
                return False

            return all(checks) and self.file_validator(message.attachments) is True

    async def transform_ask_message(self):
        pass


class AskInputManyAnswers(AskInput):
    finished_phrase = "🆗"

    def __init__(self, author: Union[int, discord.Member, discord.User], channel: Union[int, discord.DMChannel, discord.TextChannel], timeout: int = 500, validator: Callable = None) -> None:
        super().__init__(author=author, channel=channel, timeout=timeout, validator=validator)
        self.collected_text = []

    async def transform_answer(self, answer):
        if answer.content == self.cancel_phrase:
            return self.CANCELED
        if answer.content == self.finished_phrase:
            return self.FINISHED
        return answer.content

    async def make_fields(self):
        fields = [self.bot.field_item(name="You can enter as many messages as you like", value=ZERO_WIDTH, inline=False),
                  self.bot.field_item(name="When you finished", value=f"Then send a message consisting of only {self.finished_phrase}", inline=False)]
        fields += await super().make_fields()
        return fields

    def check_if_answer(self, message: discord.Message):
        return super().check_if_answer(message) or (super().check_if_answer(message) is True and str(self.finished_phrase) in message.content)

    async def update_ask_embed_data(self):
        if self.collected_text:
            embed = self.ask_embed_data.get('embed')
            embed.remove_field(0)
            new_text = alternative_better_shorten('\n'.join(self.collected_text), max_length=1000, shorten_side='left')
            log.debug("new_text has a len of %s", len(new_text))
            embed.insert_field_at(0, name='Stored text', value=new_text, inline=False)
            await self.ask_message.edit(**self.ask_embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def ask(self, **kwargs):
        self.ask_embed_data = await self.make_ask_embed(**kwargs)
        self.ask_message = await self.channel.send(**self.ask_embed_data)
        await self.transform_ask_message()
        while True:
            answer = await self._ask_mechanism()
            transformed_answer = await self.transform_answer(answer)
            if transformed_answer is self.CANCELED:
                return transformed_answer
            if transformed_answer is self.FINISHED:
                break

            self.collected_text.append(transformed_answer)
        return '\n'.join(self.collected_text)
