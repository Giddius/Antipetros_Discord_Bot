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

from io import BytesIO, IOBase
from abc import ABC, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Union, Callable, Iterable, Optional, TYPE_CHECKING, IO
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
import inspect
# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord
from discord.ext import commands

# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty, check_if_url, fix_url_prefix
from antipetros_discordbot.utility.gidtools_functions import bytes2human
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI, letter_to_emoji, CANCEL_EMOJI, FINISHED_EMOJI
from antipetros_discordbot.utility.exceptions import MissingNeededAttributeError, NeededClassAttributeNotSet, AskCanceledError, AskTimeoutError
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import shorten_string
from antipetros_discordbot.utility.converters import UrlConverter
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


async def try_add_reaction(message: discord.Message, reaction: Union[str, discord.Emoji, discord.PartialEmoji]):
    try:
        await message.add_reaction(reaction)
    except discord.errors.NotFound:
        log.debug("Unable to add reaction %s , for ask-item as message is not found, most likely already answered", reaction)


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
    SELECTION_AND_INPUT = auto()

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

    async def asyncio_values(self):
        for value in self.options.values():
            yield value
            await asyncio.sleep(0)

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
    cancel_phrase = CANCEL_EMOJI
    finished_phrase = "🆗"
    finished_emoji = FINISHED_EMOJI
    confirm_emoji = CHECK_MARK_BUTTON_EMOJI
    decline_emoji = CROSS_MARK_BUTTON_EMOJI
    error_answers = {AskAnswer.CANCELED, AskAnswer.NOANSWER}

    bot = None
    mandatoy_attributes = ['bot']

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 300,
                 delete_question: bool = True,
                 delete_emojis: bool = True,
                 error_on: Union[bool, list[AskAnswer], AskAnswer, frozenset[AskAnswer]] = True) -> None:
        for c_attr_name in self.mandatoy_attributes:
            if getattr(self, c_attr_name) is None:
                raise NeededClassAttributeNotSet(c_attr_name, self.__class__.__name__)
        self.timeout = timeout
        self.channel = self._ensure_channel(channel)
        self.author = self._ensure_author(author)
        self.delete_question = delete_question
        self.delete_emojis = delete_emojis
        self.error_on = self._ensure_error_on(error_on)
        self.title = None
        self.description = ZERO_WIDTH
        self.thumbnail = None
        self.fields = []
        self.extra_fields = []
        self.ask_message = None
        self.ask_embed_data = None
        self.end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=timeout)

    def set_description(self, description: str):
        self.description = description

    def set_title(self, title: str):
        self.title = title

    def set_thumbnail(self, thumbnail: Union[str, bytes, discord.File, IO]):
        self.thumbnail = thumbnail

    def add_extra_field(self, name: str, content: str):
        self.extra_fields.append(EmbedFieldItem(name=name, value=content))

    def _ensure_error_on(self, error_on: Union[bool, list[AskAnswer], AskAnswer, frozenset[AskAnswer]]) -> frozenset:
        if isinstance(error_on, frozenset):
            return error_on
        if isinstance(error_on, list):
            return frozenset(error_on)
        if isinstance(error_on, AskAnswer):
            return frozenset([error_on])
        if isinstance(error_on, bool):
            if error_on is True:
                return frozenset(self.error_answers)
            if error_on is False:
                return frozenset()
        log.critical("error_on=%s", error_on)

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
    def from_context(cls, ctx: commands.Context, **kwargs):
        author = ctx.author
        channel = ctx.channel
        return cls(author=author, channel=channel, **kwargs)

    @classmethod
    def from_other_asking(cls, other: "AbstractUserAsking", **kwargs):
        author = other.author
        channel = other.channel
        for param in list(inspect.signature(cls.__init__).parameters.keys()):
            if param not in {'self', 'author', 'channel'} and param not in kwargs:
                if hasattr(other, param):
                    kwargs[param] = getattr(other, param)
        return cls(author=author, channel=channel, **kwargs)

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

    async def on_cancel(self, answer):
        if AskAnswer.CANCELED in self.error_on:
            raise AskCanceledError(self, answer)

        return self.CANCELED

    async def make_fields(self):
        return [self.bot.field_item(name="Time to answer", value=alt_seconds_to_pretty(int(self.timeout)), inline=False),
                self.bot.field_item(name=f"{self.cancel_emoji} to Cancel", value=ZERO_WIDTH, inline=False)] + self.extra_fields

    async def make_ask_embed(self, **kwargs):
        return await self.bot.make_asking_embed(typus=self.typus, timeout=self.timeout, description=self.description, fields=await self.make_fields(), title=self.title, **kwargs)

    async def on_timeout(self):
        if AskAnswer.NOANSWER in self.error_on:
            raise AskTimeoutError(self)

        return self.NOANSWER

    @abstractmethod
    def check_if_answer(self):
        ...

    async def update_ask_embed_data(self):
        pass

    async def _ask_mechanism(self):
        timeout = (self.end_time - datetime.now(tz=timezone.utc)).total_seconds()
        asyncio.create_task(self.update_ask_embed_data())
        try:
            return await self.bot.wait_for(event=self.wait_for_event, timeout=timeout, check=self.check_if_answer)
        except asyncio.TimeoutError:
            return await self.on_timeout()

    async def ask(self, **kwargs):
        self.ask_embed_data = await self.make_ask_embed(**kwargs)
        self.ask_message = await self.channel.send(**self.ask_embed_data)
        await self.transform_ask_message()
        answer = await self._ask_mechanism()

        try:
            _out = await self.transform_answer(answer)
        finally:
            await self.after_ask()

        return _out

    async def after_ask(self):

        if self.delete_question is True:
            try:
                await self.ask_message.delete()
            except discord.errors.Forbidden:
                pass
            except discord.errors.NotFound:
                pass

        if self.delete_emojis is True:
            try:
                msg = await self.channel.fetch_message(self.ask_message.id)
                log.debug("Trying to delete emojis")

                for reaction in msg.reactions:
                    async for user in reaction.users():
                        if user.id == self.bot.user.id:
                            asyncio.create_task(msg.remove_reaction(reaction, user))
            except discord.errors.Forbidden:
                pass
            except discord.errors.NotFound:
                pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


class AskConfirmation(AbstractUserAsking):
    wait_for_event = 'raw_reaction_add'
    typus = AskingTypus.CONFIRMATION

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 300,
                 delete_question: bool = True,
                 error_on: Union[bool, list[AskAnswer], AskAnswer] = True) -> None:
        super().__init__(timeout=timeout, author=author, channel=channel, delete_question=delete_question, error_on=error_on)

    @cached_property
    def answer_table(self):
        return {self.confirm_emoji: self.ACCEPTED,
                self.decline_emoji: self.DECLINED}

    async def transform_answer(self, answer):
        answer_emoji = str(answer.emoji)

        if answer_emoji == self.cancel_emoji:
            return await self.on_cancel(answer)
        return self.answer_table.get(answer_emoji)

    def check_if_answer(self, payload: discord.RawReactionActionEvent):
        checks = [payload.user_id == self.author.id,
                  payload.channel_id == self.channel.id,
                  payload.message_id == self.ask_message.id,
                  str(payload.emoji) in self.answer_table or str(payload.emoji) == self.cancel_emoji]

        return all(checks)

    async def transform_ask_message(self):
        for emoji in self.answer_table:
            asyncio.create_task(try_add_reaction(self.ask_message, emoji))
        asyncio.create_task(try_add_reaction(self.ask_message, self.cancel_emoji))


class AskInput(AbstractUserAsking):
    wait_for_event = 'message'
    typus = AskingTypus.INPUT

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 300,
                 delete_question: bool = True,
                 delete_answers: bool = False,
                 validator: Callable = None,
                 error_on: Union[bool, list[AskAnswer], AskAnswer] = True) -> None:
        super().__init__(timeout=timeout, author=author, channel=channel, delete_question=delete_question, error_on=error_on)
        self.validator = self.default_validator if validator is None else validator
        self.delete_answers = delete_answers
        self.answer_messages = []

    async def make_fields(self):
        fields = await super().make_fields()
        fields = [fields[0], self.bot.field_item(name=f"Type {self.cancel_phrase} to cancel", value=ZERO_WIDTH, inline=False)]
        return fields

    def default_validator(self, content):
        return content != ""

    async def transform_answer(self, answer):
        self.answer_messages.append(answer)
        if answer.content == self.cancel_phrase:
            return await self.on_cancel(answer)

        return answer.content

    def check_if_answer(self, message: discord.Message):
        checks = [message.author.id == self.author.id,
                  message.channel.id == self.channel.id]
        if all(checks):
            return self.validator(message.content) is True or message.content == self.cancel_phrase

    async def after_ask(self):
        await super().after_ask()

        if self.delete_answers is True:
            for answer in self.answer_messages:
                try:
                    await answer.delete()
                except discord.errors.NotFound:
                    continue
                except discord.errors.Forbidden:
                    continue

    async def transform_ask_message(self):
        pass


class AskFile(AbstractUserAsking):
    typus = AskingTypus.FILE
    wait_for_event = 'message'
    allowed_file_types = frozenset({'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'tiff', 'tga', 'txt', 'md', 'log', 'rpt'})
    cancel_phrase = 'CANCEL'
    finished_phrase = "CONTINUE"

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 300,
                 delete_question: bool = True,
                 delete_answers: bool = False,
                 file_validator: Callable = None,
                 error_on: Union[bool, list[AskAnswer], AskAnswer] = True) -> None:
        super().__init__(author=author, channel=channel, timeout=timeout, delete_question=delete_question, error_on=error_on)
        self.delete_answers = delete_answers
        self.file_validator = self.default_file_validator if file_validator is None else file_validator
        self.collected_attachments = []
        self.answer_messages = []

    async def make_fields(self):
        fields = [self.bot.field_item(name="Attached Files", value="None", inline=False)]
        super_fields = await super().make_fields()
        fields += [super_fields[0], self.bot.field_item(name=f"Type {self.cancel_phrase} to cancel", value=ZERO_WIDTH, inline=False)]
        fields.append(self.bot.field_item(name="Once you are done attaching Files, or do not have any files to attach", value=f"click the emoji {self.finished_emoji} or send a message only containing **{self.finished_phrase}**", inline=False))
        fields.append(self.bot.field_item(name="allowed File Types", value=','.join(f"`{ftype}`" for ftype in self.allowed_file_types), inline=False))
        return fields

    async def download_image(self, url):
        pass

    async def transform_answer(self, answer):
        self.answer_messages.append(answer)
        if answer.content == self.cancel_phrase:
            return await self.on_cancel(answer)

        if answer.content.casefold() == self.finished_phrase.casefold() and answer.attachments == []:
            return AskAnswer.FINISHED
        _out = []
        for attachment in answer.attachments:
            file_type = attachment.filename.casefold().split('.')[-1]
            if file_type not in self.allowed_file_types:
                asyncio.create_task(self.channel.send(f'file-type {file_type!r} is not allowed.'))
            elif self.channel.type is discord.ChannelType.private and attachment.size >= 8388608:
                asyncio.create_task(self.channel.send(
                    f'Please keep the file size under 8mb (received file size= {bytes2human(attachment.size,True)}).\nIf you need to upload larger files, upload them somewhere and use add the link to the remark text.'))
            else:
                _out.append(attachment)
        return _out

    async def on_timeout(self):
        return self.NOANSWER

    def default_file_validator(self, attachments):
        if attachments is None or attachments == []:
            return True

        # return all(attachment.filename.casefold().split('.')[-1] in self.allowed_file_types for attachment in attachments)
        return True

    def check_if_answer(self, message: discord.Message):
        checks = [message.author.id == self.author.id,
                  message.channel.id == self.channel.id]

        if all(checks):
            if message.content.upper() not in {self.finished_phrase, self.cancel_phrase} and not message.attachments:
                return False

            return True

    async def transform_ask_message(self):
        pass

    async def update_ask_embed_data(self):
        if self.collected_attachments:
            embed = self.ask_embed_data.get('embed')
            embed.remove_field(0)
            new_text = ListMarker.make_list([f"`{attachment.filename}`" for attachment in self.collected_attachments])
            new_text = shorten_string(new_text, max_length=1000, shorten_side='left', split_on='\n')
            embed.insert_field_at(0, name='Stored Attachments', value=new_text, inline=False)
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

            self.collected_attachments += transformed_answer

            if len(self.collected_attachments) == 10:
                break
        asyncio.create_task(self.after_ask())
        return self.collected_attachments

    async def after_ask(self):
        await super().after_ask()
        if self.delete_answers is True:
            for answer in self.answer_messages:
                try:
                    await answer.delete()
                except discord.errors.NotFound:
                    continue
                except discord.errors.Forbidden:
                    continue


class AskInputManyAnswers(AskInput):

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 500,
                 delete_question: bool = True,
                 delete_answers: bool = False,
                 error_on: Union[bool, list[AskAnswer], AskAnswer] = True) -> None:
        super().__init__(author=author, channel=channel, timeout=timeout, delete_question=delete_question, delete_answers=delete_answers, error_on=error_on)
        self.collected_text = []

    async def transform_answer(self, answer):
        self.answer_messages.append(answer)
        if answer.content == self.cancel_phrase:
            return await self.on_cancel(answer)
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
            new_text = shorten_string('\n'.join(self.collected_text), max_length=1000, shorten_side='left')

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


class AskSelection(AbstractUserAsking):
    typus = AskingTypus.SELECTION
    option_item = AskSelectionOption
    wait_for_event = 'raw_reaction_add'

    def __init__(self,
                 author: Union[int, discord.Member, discord.User],
                 channel: Union[int, discord.DMChannel, discord.TextChannel],
                 timeout: int = 300,
                 delete_question: bool = True,
                 default_emojis: list[str, discord.Emoji] = None,
                 error_on: Union[bool, list[AskAnswer], AskAnswer] = True) -> None:
        super().__init__(author, channel, timeout=timeout, delete_question=delete_question, error_on=error_on)
        self.options = AskSelectionOptionsMapping(default_emojis=default_emojis)

    async def make_fields(self):
        fields = await self.options.to_fields()
        fields += await super().make_fields()
        return fields

    def check_if_answer(self, payload: discord.RawReactionActionEvent):

        checks = [payload.message_id == self.ask_message.id,
                  payload.user_id == self.author.id,
                  payload.emoji in self.options or str(payload.emoji) == self.cancel_emoji]
        return all(checks)

    async def transform_ask_message(self):
        for emoji in self.options:
            asyncio.create_task(try_add_reaction(self.ask_message, emoji))
        asyncio.create_task(try_add_reaction(self.ask_message, self.cancel_emoji))

    async def transform_answer(self, answer: discord.RawReactionActionEvent):
        answer_emoji = str(answer.emoji)

        if answer_emoji == self.cancel_emoji:
            return await self.on_cancel(answer)
        return self.options.get_result(answer_emoji)


class AskFileWithEmoji(AskFile):
    extra_wait_for_event = 'raw_reaction_add'

    async def transform_ask_message(self):
        asyncio.create_task(try_add_reaction(self.ask_message, self.cancel_emoji))
        asyncio.create_task(try_add_reaction(self.ask_message, self.finished_emoji))

    def check_if_answer_emoji(self, payload: discord.RawReactionActionEvent):
        checks = [payload.user_id == self.author.id,
                  payload.channel_id == self.channel.id,
                  payload.message_id == self.ask_message.id,
                  str(payload.emoji) in {self.finished_emoji, self.cancel_emoji}]

        return all(checks)

    async def transform_answer(self, answer):
        if isinstance(answer, discord.Message):
            return await super().transform_answer(answer=answer)

        answer_emoji = str(answer.emoji)

        if answer_emoji == self.cancel_emoji:
            return await self.on_cancel(answer)
        if answer_emoji == self.finished_emoji:
            return AskAnswer.FINISHED

    async def _ask_mechanism(self):
        timeout = (self.end_time - datetime.now(tz=timezone.utc)).total_seconds()
        asyncio.create_task(self.update_ask_embed_data())

        _futures = [asyncio.ensure_future(self.bot.wait_for(event=self.wait_for_event, timeout=timeout, check=self.check_if_answer)),
                    asyncio.ensure_future(self.bot.wait_for(event=self.extra_wait_for_event, timeout=timeout, check=self.check_if_answer_emoji))]
        try:
            done, pending = await asyncio.wait(_futures, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            for pending_task in pending:
                if isinstance(pending_task, asyncio.Task) and pending_task.done() is False:
                    pending_task.cancel()
            return await list(done)[0]

        except asyncio.TimeoutError:
            return await self.on_timeout()


class AskInputWithEmoji(AskInput):
    extra_wait_for_event = 'raw_reaction_add'

    async def transform_ask_message(self):
        asyncio.create_task(try_add_reaction(self.ask_message, self.cancel_emoji))

    def check_if_answer_emoji(self, payload: discord.RawReactionActionEvent):
        checks = [payload.user_id == self.author.id,
                  payload.channel_id == self.channel.id,
                  payload.message_id == self.ask_message.id,
                  str(payload.emoji) in {self.cancel_emoji}]

        return all(checks)

    async def _ask_mechanism(self):
        timeout = (self.end_time - datetime.now(tz=timezone.utc)).total_seconds()
        asyncio.create_task(self.update_ask_embed_data())

        _futures = [asyncio.ensure_future(self.bot.wait_for(event=self.wait_for_event, timeout=timeout, check=self.check_if_answer)),
                    asyncio.ensure_future(self.bot.wait_for(event=self.extra_wait_for_event, timeout=timeout, check=self.check_if_answer_emoji))]
        try:
            done, pending = await asyncio.wait(_futures, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            for pending_task in pending:
                if isinstance(pending_task, asyncio.Task) and pending_task.done() is False:
                    pending_task.cancel()
            return await list(done)[0]

        except asyncio.TimeoutError:
            return await self.on_timeout()

    async def transform_answer(self, answer):
        if isinstance(answer, discord.Message):
            return await super().transform_answer(answer=answer)

        answer_emoji = str(answer.emoji)

        if answer_emoji == self.cancel_emoji:
            return await self.on_cancel(answer)
