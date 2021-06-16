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
    option_item = AskSelectionOption
    cancel_emoji = "🛑"
    confirm_emoji = CHECK_MARK_BUTTON_EMOJI
    decline_emoji = CROSS_MARK_BUTTON_EMOJI

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.temp_messages = []
        self.temp_reactions = []
        self.continous_typing_task = None
        self.use_continous_typing = False

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

    async def delete_temp_items(self):

        async def _remove_temp_reaction(reaction, delay: int = 15):
            await asyncio.sleep(delay)
            try:
                await self.message.remove_reaction(reaction, self.bot)
            except discord.errors.NotFound:
                pass

        async def _remove_temp_msg(msg, delay: int = 30):
            await asyncio.sleep(delay)
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass
        for message in self.temp_messages:
            asyncio.create_task(_remove_temp_msg(message, 30))
        for emoji in self.temp_reactions:
            asyncio.create_task(_remove_temp_reaction(emoji, 15))

    async def send(self, content=None, *, tts=False, embed=None, file=None,
                   files=None, delete_after=None, nonce=None,
                   allowed_mentions=discord.AllowedMentions.none(), reference=None,
                   mention_author=False):
        _out = await super().send(content=content,
                                  tts=tts,
                                  embed=embed,
                                  file=file,
                                  files=files,
                                  delete_after=delete_after,
                                  nonce=nonce,
                                  allowed_mentions=allowed_mentions,
                                  reference=reference,
                                  mention_author=mention_author)
        if self.use_continous_typing is True:
            asyncio.create_task(self.trigger_typing())
        return _out

    async def reply(self, content=None, mention_author=False, ** kwargs):

        allowed_mentions = kwargs.pop('allowed_mentions', discord.AllowedMentions.none())
        allowed_mentions.replied_user = mention_author
        _out = await self.message.reply(content, allowed_mentions=allowed_mentions, ** kwargs)
        if self.use_continous_typing is True:
            asyncio.create_task(self.trigger_typing())
        return _out

    async def ask_confirmation(self, description: str, timeout: float = 300.0, **kwargs):
        options_map = {self.confirm_emoji: ContextAskAnswer.ACCEPTED,
                       self.decline_emoji: ContextAskAnswer.DECLINED}

        fields = kwargs.get('fields', [])
        fields.append(self.bot.field_item(name="Time to answer", value=alt_seconds_to_pretty(int(timeout)), inline=False))
        fields.append(self.bot.field_item(name=f"{self.cancel_emoji} to Cancel", value=ZERO_WIDTH, inline=False))

        embed_data = await self.bot.make_generic_embed(title=kwargs.get('title', "Confirmation Required"),
                                                       description=description,
                                                       thumbnail=kwargs.get('thumbnail', "question"),
                                                       fields=fields,
                                                       footer=kwargs.get('footer', {'text': "Times out at -> "}),
                                                       timestamp=kwargs.get('timestamp', datetime.now(tz=timezone.utc) + timedelta(seconds=int(timeout))),
                                                       color=kwargs.get('color', None),
                                                       image=kwargs.get('image', None),
                                                       author=kwargs.get("author", "not_set"),
                                                       url=kwargs.get('url', None),
                                                       files=kwargs.get('files', []),
                                                       file=kwargs.get('file', None))

        ask_confirmation_message = await self.send(**embed_data)
        for emoji in options_map:
            asyncio.create_task(ask_confirmation_message.add_reaction(emoji))
        asyncio.create_task(ask_confirmation_message.add_reaction(self.cancel_emoji))

        def check_confirm(payload: discord.RawReactionActionEvent):
            checks = [payload.message_id == ask_confirmation_message.id,
                      payload.user_id == self.author.id,
                      str(payload.emoji) in options_map or str(payload.emoji) == self.cancel_emoji]
            return all(checks)

        try:
            payload = await self.bot.wait_for('raw_reaction_add', timeout=timeout, check=check_confirm)
            if str(payload.emoji) == self.cancel_emoji:
                return ContextAskAnswer.CANCELED
            return options_map.get(str(payload.emoji))
        except asyncio.TimeoutError:
            return ContextAskAnswer.NOANSWER
        finally:
            await ask_confirmation_message.delete()

    async def ask_selection(self,
                            description: str,
                            options: list[AskSelectionOption],
                            emoji_list: Optional[Iterable[Union[str, discord.Emoji]]] = None,
                            timeout: float = 300.0,
                            update_time_left: bool = False,
                            raise_for: Optional[Union[ContextAskAnswer, bool]] = False, **kwargs):
        options_holder = AskSelectionOptionsMapping(default_emojis=emoji_list)
        options_holder.add_many_options(options)
        fields = kwargs.get('fields', [])

        fields += await options_holder.to_fields()

        fields.append(self.bot.field_item(name=f"{self.cancel_emoji} to Cancel", value=ZERO_WIDTH, inline=False))
        fields.append(self.bot.field_item(name="Time to answer", value=alt_seconds_to_pretty(int(timeout)), inline=False))
        end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=int(timeout))
        embed_data = await self.bot.make_generic_embed(title=kwargs.get('title', "Please Select"),
                                                       description=description,
                                                       thumbnail=kwargs.get('thumbnail', "question"),
                                                       fields=fields,
                                                       footer=kwargs.get('footer', {'text': "Times out at -> "}),
                                                       timestamp=kwargs.get('timestamp', end_time),
                                                       color=kwargs.get('color', None),
                                                       image=kwargs.get('image', None),
                                                       author=kwargs.get("author", "not_set"),
                                                       url=kwargs.get('url', None),
                                                       files=kwargs.get('files', []),
                                                       file=kwargs.get('file', None))
        ask_selection_message = await self.send(**embed_data)
        for emoji in options_holder:
            asyncio.create_task(ask_selection_message.add_reaction(emoji))
        asyncio.create_task(ask_selection_message.add_reaction(self.cancel_emoji))
        if update_time_left is True:

            async def _update_time_left(refresh_rate: int = 30):

                async def _get_seconds_left():
                    time_left = end_time - datetime.now(tz=timezone.utc)
                    return time_left.total_seconds()

                embed = embed_data.get('embed').copy()
                while True:
                    embed.remove_field(-1)
                    seconds_left = await _get_seconds_left()

                    if seconds_left <= 30:
                        refresh_rate = 1
                    elif seconds_left <= 60:
                        refresh_rate = 5
                    elif seconds_left <= 120:
                        refresh_rate = 10
                    elif seconds_left <= 240:
                        refresh_rate = 20
                    await asyncio.sleep((seconds_left % refresh_rate) - 1)
                    embed.add_field(name="Time to answer", value=alt_seconds_to_pretty(await _get_seconds_left()), inline=False)
                    try:
                        await ask_selection_message.edit(embed=embed)
                    except discord.errors.NotFound:
                        log.debug('ask_selection_message not found, cancelling update task')
                        break
                    except discord.errors.HTTPException:
                        log.debug('ask_selection_message not found, cancelling update task')
                        break

            update_task = asyncio.create_task(_update_time_left(30))

        def check_select(payload: discord.RawReactionActionEvent):
            checks = [payload.message_id == ask_selection_message.id,
                      payload.user_id == self.author.id,
                      payload.emoji in options_holder or str(payload.emoji) == self.cancel_emoji]
            return all(checks)

        try:
            payload = await self.bot.wait_for('raw_reaction_add', timeout=(end_time - datetime.now(tz=timezone.utc)).total_seconds(), check=check_select)
            if str(payload.emoji) == self.cancel_emoji:
                if raise_for in {True, ContextAskAnswer.CANCELED}:
                    raise ParameterError  # AskCanceledError(self)
                return ContextAskAnswer.CANCELED
            return options_holder.get_result(payload.emoji)
        except asyncio.TimeoutError as error:
            if raise_for in {True, ContextAskAnswer.NOANSWER}:
                raise error
            return ContextAskAnswer.NOANSWER
        finally:
            if update_time_left is True and update_task.cancelled() is False and update_task.done() is False:
                update_task.cancel()
            await ask_selection_message.delete()

    async def ask_input(self,
                        description: str,
                        validator: Union[str, re.Pattern, Callable],
                        case_insensitive: bool = True,
                        timeout: float = 300.0,
                        update_time_left: bool = False,
                        raise_for: Optional[Union[ContextAskAnswer, bool]] = False,
                        **kwargs):
        fields = kwargs.get('fields', [])
        fields.append(self.bot.field_item(name="Type `CANCEL` to cancel", value=ZERO_WIDTH, inline=False))
        fields.append(self.bot.field_item(name="Time to answer", value=alt_seconds_to_pretty(int(timeout)), inline=False))
        end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=int(timeout))
        embed_data = await self.bot.make_generic_embed(title=kwargs.get('title', "Please Select"),
                                                       description=description,
                                                       thumbnail=kwargs.get('thumbnail', "question"),
                                                       fields=fields,
                                                       footer=kwargs.get('footer', {'text': "Times out at -> "}),
                                                       timestamp=kwargs.get('timestamp', end_time),
                                                       color=kwargs.get('color', None),
                                                       image=kwargs.get('image', None),
                                                       author=kwargs.get("author", "not_set"),
                                                       url=kwargs.get('url', None),
                                                       files=kwargs.get('files', []),
                                                       file=kwargs.get('file', None))

        ask_input_message = await self.send(**embed_data)

        def check_input(message: discord.Message):
            checks = [message.channel.id == ask_input_message.channel.id,
                      message.author.id == self.message.author.id]

            if all(checks):
                if message.content == 'CANCEL':

                    return True

                if callable(validator):

                    return validator(message)

                if isinstance(validator, re.Pattern):

                    validator_match = validator.search(message.content)
                    return validator_match is not None

                if isinstance(validator, str):

                    content = message.content.casefold() if case_insensitive is True else message.content
                    return content == validator

                return False
            else:

                return False

        try:
            message = await self.bot.wait_for(event='message', timeout=(end_time - datetime.now(tz=timezone.utc)).total_seconds(), check=check_input)
            if message.content == 'CANCEL':
                if raise_for in {True, ContextAskAnswer.CANCELED}:
                    raise ParameterError  # AskCanceledError(self)
                return ContextAskAnswer.CANCELED
            return message.content
        except asyncio.TimeoutError as error:
            if raise_for in {True, ContextAskAnswer.NOANSWER}:
                raise error
            return ContextAskAnswer.NOANSWER
        finally:
            # if update_time_left is True and update_task.cancelled() is False and update_task.done() is False:
            #     update_task.cancel()
            await ask_input_message.delete()

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
