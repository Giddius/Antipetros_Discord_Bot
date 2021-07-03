# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
import random
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
from time import sleep
from pprint import pprint, pformat
from typing import Optional, Union, Any, TYPE_CHECKING, Callable, Iterable, List, Dict, Set, Tuple, Mapping, AsyncGenerator
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import unicodedata
from io import BytesIO, StringIO
from textwrap import dedent


import dateparser

import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property
from dateparser import parse as date_parse
from hashlib import shake_256

import gidlogger as glog


from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_write_json, async_load_json, alt_seconds_to_pretty
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskInput, AskInputManyAnswers, AskFile, AskAnswer, AskSelection, AskSelectionOption
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import shorten_string
from antipetros_discordbot.utility.exceptions import AskCanceledError
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from functools import total_ordering
from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.utility.discord_markdown_helper import CodeBlock, shorten_string
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
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

# endregion[Constants]


@total_ordering
class ReminderItem:
    __slots__ = ("name", "remind_at", "user", "original_message", "reason", "reference_message", "done", "db_id")
    cog: "ReminderCog" = None

    def __init__(self,
                 name: str,
                 remind_at: datetime,
                 user: Union[discord.User, discord.Member],
                 original_message: discord.Message,
                 reason: Optional[str] = None,
                 reference_message: Optional[discord.Message] = None,
                 done: bool = False,
                 db_id: Optional[int] = None):

        self.db_id = db_id
        self.name = name
        self.remind_at = remind_at
        self.user = user
        self.original_message = original_message
        self.reason = reason
        self.reference_message = reference_message
        self.done = done

    @classmethod
    async def from_db_row(cls, row):
        try:
            original_message = await cls.cog.bot.get_message_directly(channel_id=row['original_channel_id'], message_id=row['original_message_id'])
        except discord.errors.NotFound:
            await cls.cog.db.mark_reminder_done(row['id'])
            return None
        if row['reference_message_id'] is None:
            reference_message = None
        else:
            try:
                reference_message = await cls.cog.bot.get_message_directly(channel_id=row['original_channel_id'], message_id=row['reference_message_id'])
            except discord.errors.NotFound:
                reference_message = None

        init_kwargs = {"db_id": row['id'],
                       "name": row['name'],
                       "remind_at": row['remind_at'].replace(tzinfo=timezone.utc),
                       "user": cls.cog.bot.get_antistasi_member(row['user_id']),
                       "original_message": original_message,
                       "reason": row['reason'],
                       "reference_message": reference_message}
        return cls(**init_kwargs)

    @classmethod
    async def create_new_reminder(cls,
                                  name: str,
                                  remind_at: datetime,
                                  user: Union[discord.User, discord.Member],
                                  original_message: discord.Message,
                                  reason: Optional[str] = None,
                                  reference_message: Optional[discord.Message] = None):

        reference_message_id = reference_message.id if reference_message is not None else reference_message

        await cls.cog.db.insert_reminder(name=name,
                                         remind_at=remind_at,
                                         user_id=user.id,
                                         original_channel_id=original_message.channel.id,
                                         original_message_id=original_message.id,
                                         reason=reason,
                                         reference_message_id=reference_message_id)

    async def message_exists(self):
        try:
            _ = await self.cog.bot.get_message_directly(self.original_message.channel.id, self.original_message.id)
            return True
        except discord.errors.NotFound:
            await self.mark_done()
            return False

    async def mark_done(self):
        self.done = True
        await self.cog.db.mark_reminder_done(self.db_id)

    async def _embed_data(self):
        description = f"You requested to be reminded because:\n{CodeBlock(self.reason, 'fix')}" if self.reason is not None else "You requested to be reminded"
        fields = [EmbedFieldItem('Reminder Name', value=self.name, inline=False)]
        if self.reference_message is not None:
            reference_content = await asyncio.to_thread(shorten_string, in_text=self.reference_message.content if self.reference_message.content else "Link", max_length=900)
            reference_link = embed_hyperlink(reference_content, self.reference_message.jump_url)
            fields.append(EmbedFieldItem(name="Reminder Reference Message", value=reference_link, inline=False))

        fields.append(EmbedFieldItem(name="Original Message", value=embed_hyperlink('link', self.original_message.jump_url), inline=False))

        footer = {'text': str(self.db_id)}
        return await self.cog.bot.make_generic_embed(title="This is a Reminder",
                                                     description=description,
                                                     fields=fields,
                                                     footer=footer,
                                                     thumbnail="reminder")

    async def remind(self):
        if await self.message_exists() is True:
            embed_data = await self._embed_data()
            await self.user.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
            await self.mark_done()

    async def trigger_check(self, now: datetime):

        if now >= self.remind_at:
            await self.remind()

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ReminderItem):
            return hash(self) == hash(o)
        return NotImplemented

    def __le__(self, o: object) -> bool:
        if isinstance(o, ReminderItem):
            return o.remind_at.timestamp() <= self.remind_at.timestamp()
        return NotImplemented

    def __repr__(self) -> str:
        attribute_dict = {"db_id": self.db_id,
                          "name": self.name,
                          "remind_at": self.remind_at.isoformat(timespec='seconds'),
                          "user": str(self.user),
                          "original_message": str(self.original_message),
                          "reason": self.reason,
                          "reference_message": str(self.reference_message),
                          "done": self.done}
        return f"{self.__class__.__name__}({', '.join(f'{key}={value}' for key, value in attribute_dict.items())})"


class ReminderCog(AntiPetrosBaseCog):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.OUTDATED | CogMetaStatus.CRASHING | CogMetaStatus.EMPTY | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.db = general_db


# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]

    async def initialize_reminder_item(self):
        ReminderItem.cog = self

    async def on_ready_setup(self):
        await self.initialize_reminder_item()
        await super().on_ready_setup()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=1)
    async def remind_loop(self):
        if self.completely_ready is False:
            return
        now = datetime.now(tz=timezone.utc)
        now = now.astimezone(tz=timezone.utc)
        async for reminder in self.get_reminders():
            asyncio.create_task(reminder.trigger_check(now=now))

    @tasks.loop(minutes=10)
    async def clean_old_reminders_loop(self):
        log.info("cleaning old reminders from db")
        await self.db.delete_done_reminders()

# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @ auto_meta_info_command(experimental=True, aliases=['remind_me', "remind"])
    async def new_reminder(self, ctx: commands.Context, remind_at: str, name: str, *, reason: Optional[str] = None):
        reference_message = ctx.message.reference.resolved if ctx.message.reference is not None else None
        _remind_at = date_parse(remind_at, settings={'TIMEZONE': 'UTC'})
        if _remind_at is None:
            await ctx.send(f"Unable to parse datetime `{remind_at}`", delete_after=90)
            return
        _remind_at = _remind_at.replace(tzinfo=timezone.utc)
        if _remind_at <= datetime.now(tz=timezone.utc):
            await ctx.send(f"The specified time `{remind_at}` is in the past, **I can not notify you at that time without breaking Causality**")
            return

        await ReminderItem.create_new_reminder(name=name, remind_at=_remind_at, user=ctx.author, original_message=ctx.message, reason=reason, reference_message=reference_message)
        embed_data = await self.new_reminder_embed(remind_at=_remind_at, name=name, reason=reason, reference_message=reference_message)
        await ctx.send(**embed_data)

# endregion [Commands]

# region [DataStorage]

    async def get_reminders(self) -> AsyncGenerator[ReminderItem, None]:
        for reminder in await self.db.get_all_reminders(reminder_item=ReminderItem):
            yield reminder


# endregion [DataStorage]

# region [HelperMethods]

    async def _get_relative_time(self, absolute_time: datetime, pretty: bool = True) -> Union[int, str]:
        now = datetime.now(tz=absolute_time.tzinfo)
        if now > absolute_time:
            rel_time = now - absolute_time
        else:
            rel_time = absolute_time - now
        rel_time_seconds = rel_time.total_seconds()
        if pretty is False:
            return rel_time_seconds

        return alt_seconds_to_pretty(rel_time_seconds, last_separator=' and ')

    async def new_reminder_embed(self, remind_at: datetime, name: str, reason: Optional[str] = None, reference_message: Optional[discord.Message] = None):
        title = "Reminder Set"
        description = f"Your Reminder `{name}` was created. I will Remind you at the set Time!"

        times = {'UTC': remind_at.strftime(self.bot.std_date_time_format_utc),
                 'Relative': await self._get_relative_time(remind_at, pretty=True),
                 'Local Time': "⇓ See Timestamp ⇓"}
        fields = [EmbedFieldItem(name="Reminding At", value=ListMarker.make_list([f"{key}: `{value}`" for key, value in times.items()], indent=1), inline=False),
                  EmbedFieldItem(name="Reason", value=reason, inline=False)]

        if reference_message is not None:
            fields.append(EmbedFieldItem(name="Reference Message", value=embed_hyperlink("Link", reference_message.jump_url), inline=False))

        return await self.bot.make_generic_embed(title=title, description=description, fields=fields, thumbnail="reminder", timestamp=remind_at)


# endregion [HelperMethods]

# region [SpecialMethods]


    def cog_check(self, ctx: commands.Context):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(ReminderCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
