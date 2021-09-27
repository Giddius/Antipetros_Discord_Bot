"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Any, Callable, Iterable, io
import gc
import os
import unicodedata
import asyncio
import re
from enum import Enum, auto
# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->
from functools import cached_property
import discord

from discord.ext import commands, tasks

# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->
from contextlib import asynccontextmanager
import gidlogger as glog
import collections.abc
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI, letter_to_emoji
from antipetros_discordbot.utility.enums import ContextAskAnswer
from antipetros_discordbot.utility.exceptions import ParameterError
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.auxiliary_classes.asking_items import AskSelectionOption, AskSelectionOptionsMapping
from antipetros_discordbot.schemas import AntiPetrosBaseContextSchema
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AntiPetrosBaseContext(commands.Context):

    schema = AntiPetrosBaseContextSchema()

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.temp_messages = []
        self.temp_reactions = []
        self.continous_typing_task = None
        self.use_continous_typing = False
        self.stored_messages = []
        self.store_all = False

    def enable_store_all(self):
        self.store_all = True

    def disable_store_all(self):
        self.store_all = False

    async def _continous_typing(self):
        while True:
            await asyncio.sleep(5)
            await self.trigger_typing()

    @asynccontextmanager
    async def continous_typing(self):
        self.use_continous_typing = True
        await self.trigger_typing()
        self.continous_typing_task = asyncio.create_task(self._continous_typing())
        yield
        self.use_continous_typing = False
        self.continous_typing_task.cancel()

    async def add_temp_reaction(self, reaction):
        await self.message.add_reaction(reaction)
        self.temp_reactions.append(reaction)

    async def temp_send(self, content=None, **kwargs):
        msg = await self.send(content=content, **kwargs)
        self.temp_messages.append(msg)
        if self.continous_typing_task is not None:
            await self.trigger_typing()

    async def delete_stored_messages(self, delay: int = None):
        async def _delete_stored_message(message: discord.Message):
            done, pending = await asyncio.wait([self.bot.is_shutting_down_event.wait()], timeout=delay, return_when=asyncio.FIRST_COMPLETED)
            for pending_aws in pending:
                pending_aws.cancel()
            try:
                await message.delete()
            except discord.errors.NotFound:
                log.debug("Message %s could not be deleted, as it was Not Found", message)
            except discord.errors.Forbidden:
                log.debug("Message %s could not be deleted, as it was Forbidden", message)

        for msg in self.stored_messages:
            asyncio.create_task(_delete_stored_message(msg), name=f'STORED_MESSAGE_REMOVAL_{msg.channel.name}_{msg.id}')

    async def delete_temp_items(self):

        async def _remove_temp_reaction(reaction, delay: int = 15):
            done, pending = await asyncio.wait([self.bot.is_shutting_down_event.wait()], timeout=delay, return_when=asyncio.FIRST_COMPLETED)
            for pending_aws in pending:
                pending_aws.cancel()
            try:
                await self.message.remove_reaction(reaction, self.bot)
            except discord.errors.NotFound:
                pass

        async def _remove_temp_msg(msg, delay: int = 30):
            done, pending = await asyncio.wait([self.bot.is_shutting_down_event.wait()], timeout=delay, return_when=asyncio.FIRST_COMPLETED)
            for pending_aws in pending:
                pending_aws.cancel()
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass

        for message in self.temp_messages:
            asyncio.create_task(_remove_temp_msg(message, 30), name=f'TEMP_MESSAGE_REMOVAL_{message.channel.name}_{message.id}')
        for emoji in self.temp_reactions:
            asyncio.create_task(_remove_temp_reaction(emoji, 15), name=f'TEMP_EMOJI_REMOVAL_{emoji}')

    async def delete_after(self, msg: discord.Message, delay: float = None):
        done, pending = await asyncio.wait([self.bot.is_shutting_down_event.wait()], timeout=delay, return_when=asyncio.FIRST_COMPLETED)
        for pending_aws in pending:
            pending_aws.cancel()
        try:
            await msg.delete()
        except discord.errors.NotFound:
            log.debug("Message %s could not be deleted, as it was Not Found", msg)
        except discord.errors.Forbidden:
            log.debug("Message %s could not be deleted, as it was Forbidden", msg)

    async def send(self, content=None, *, tts=False, embed=None, file=None,
                   files=None, delete_after=None, nonce=None,
                   allowed_mentions=discord.AllowedMentions.none(), reference=None,
                   mention_author=False, store: bool = False) -> discord.Message:
        _out = await super().send(content=content,
                                  tts=tts,
                                  embed=embed,
                                  file=file,
                                  files=files,
                                  nonce=nonce,
                                  allowed_mentions=allowed_mentions,
                                  reference=reference,
                                  mention_author=mention_author)
        if self.use_continous_typing is True:
            asyncio.create_task(self.trigger_typing())
        if store is True or self.store_all is True:
            self.stored_messages.append(_out)
        if delete_after is not None:
            asyncio.create_task(self.delete_after(_out, delete_after), name=f'DELETE_AFTER_MESSAGE_REMOVAL_{_out.channel.name}_{_out.id}')
        return _out

    async def reply(self, content=None, mention_author=False, store: bool = False, ** kwargs) -> discord.Message:

        allowed_mentions = kwargs.pop('allowed_mentions', discord.AllowedMentions.none())
        allowed_mentions.replied_user = mention_author
        _out = await self.message.reply(content, allowed_mentions=allowed_mentions, ** kwargs)
        if self.use_continous_typing is True:
            asyncio.create_task(self.trigger_typing())
        if store is True or self.store_all is True:
            self.stored_messages.append(_out)
        return _out

    async def dump(self):
        return self.schema.dump(self)


class AntiPetrosAdvancedContext(AntiPetrosBaseContext):

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.settings = None

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
