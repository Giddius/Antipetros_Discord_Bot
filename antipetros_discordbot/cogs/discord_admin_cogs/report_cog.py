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
from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from pprint import pprint, pformat
from typing import Optional, Union, Any, TYPE_CHECKING, Callable, Iterable, List, Dict, Set, Tuple, Mapping
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

from jinja2 import Environment, BaseLoader
import dateparser

import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property
from dateparser import parse as date_parse
from hashlib import shake_256

import gidlogger as glog
from pathlib import Path
from zipfile import ZipFile, ZIP_LZMA
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_write_json, async_load_json
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskInput, AskInputManyAnswers, AskFile, AskAnswer, AskSelection, AskSelectionOption, AskFileWithEmoji, AskInputWithEmoji
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import shorten_string
from antipetros_discordbot.utility.exceptions import AskCanceledError
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


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


class ReportItem:
    cog: "ReportCog" = None
    user_profile_base_url = "https://discordapp.com/users/"

    def __init__(self, author: discord.Member, channel: discord.DMChannel):
        self.author = author
        self.channel = channel
        self.report_id = self._determine_report_id()
        self.target = None
        self.target_type = None
        self.location = None
        self.location_type = None
        self.time = None
        self.text = ""
        self.public_text = ""
        self.files = []

    def _determine_report_id(self):
        current_date = datetime.now(tz=timezone.utc)
        id_string = current_date.isoformat() + str(self.author.id)
        id_bytes = id_string.encode('utf-8', errors='ignore')
        id_hash = shake_256(id_bytes).hexdigest(8)
        return int(id_hash, 16)

    @classmethod
    async def from_ctx(cls, ctx: commands.Context):
        author = ctx.author
        channel = ctx.channel if ctx.channel.type is discord.ChannelType.private else await cls.cog.bot.ensure_dm_channel(author)
        return cls(author=author, channel=channel)

    async def _confirm_target_member(self, name: str):
        possible_member = self.cog.bot.member_by_name(name.casefold())
        confirm_ask = AskConfirmation(self.author, self.channel, timeout=600, delete_question=True, error_on=True)
        confirm_ask.description = f"Is this the member you want to make a report against?\n\n☛ {possible_member.mention}"
        answer = await confirm_ask.ask()
        if answer is confirm_ask.ACCEPTED:
            self.target = possible_member
            self.target_type = "discord_member"
            return True
        else:
            return False

    def no_bot_invocation_validator(self, text: str):

        for prefix in self.cog.bot.all_prefixes_for_check:
            if text.startswith(prefix):
                return False
        return True

    async def _ask_for_target(self):
        input_ask = AskInput(author=self.author, channel=self.channel, timeout=600, delete_question=True, delete_answers=True, error_on=True)
        input_ask.set_title("Who do you want to make a report about?")
        input_ask.set_description("Please only specify one Person, Best practice is to use the name, with discriminator(eg: `Giddi#5858`)\nYou can get this full name by clicking on the user!")

        input_ask.validator = self.no_bot_invocation_validator
        answer = await input_ask.ask()
        if answer.casefold() in self.cog.bot.members_name_dict and await self._confirm_target_member(answer) is True:
            return

        self.target = answer
        decision_ask = AskConfirmation.from_other_asking(input_ask)
        decision_ask.description = "The provided name does not seem to be a member of the antistasi Discord. Is this an ingame name?"
        decision_answer = await decision_ask.ask()
        if decision_answer is decision_ask.ACCEPTED:
            self.target_type = "ingame_name"
        else:
            self.target_type = "other"

    async def _ask_for_location(self):
        selection_ask = AskSelection(self.author, self.channel, timeout=600, delete_question=True, error_on=True)
        for location in ["discord_channel", "discord_dm", "teamspeak", "community_server", "event", "other"]:
            location = location.replace('_', " ").title()
            selection_ask.options.add_option(AskSelectionOption(item=location))
        selection_ask.set_title("Please select the Place where the incident happened!")
        selection_ask.set_description("if the place is not in the list, please select other and you will be prompted for an input")
        main_answer = await selection_ask.ask()
        main_answer = main_answer.casefold().replace(' ', '_')

        if main_answer in {"discord_dm", "teamspeak"}:
            self.location = main_answer
            self.location_type = main_answer
            return

        if main_answer == "community_server":
            selection_ask = AskSelection(self.author, self.channel, timeout=600, delete_question=True)
            selection_ask.set_title("Please select the Server where the incident happened.")
            for server in self.cog.possible_servers:
                selection_ask.options.add_option(AskSelectionOption(item=server, name=server.pretty_name))

            server_answer = await selection_ask.ask()
            self.location = server_answer
            self.location_type = main_answer
            return

        input_ask = AskInput(self.author, self.channel, timeout=600, delete_question=True, delete_answers=True, error_on=True)
        input_ask.set_title("Please describe where exactly the incident happend.")
        input_ask.validator = self.no_bot_invocation_validator
        if main_answer == "discord_channel":
            input_ask.description = "Please input the name of the channel where the incident happened. It will only accept an answer if it is an existing channel."
            input_ask.validator = lambda x: x.casefold() in self.cog.bot.channels_name_dict

        elif main_answer == "event":
            input_ask.set_title("Please input the name of the event, where the incident happened")

        input_answer = await input_ask.ask()
        if main_answer == "discord_channel":
            self.location = self.cog.bot.channel_from_name(input_answer)
            self.location_type = main_answer
        else:
            self.location = input_answer
            self.location_type = main_answer

    async def _ask_time(self):
        input_ask = AskInput(self.author, self.channel, timeout=600, delete_question=True, delete_answers=True, error_on=True)
        input_ask.set_title("Please enter the approximate time the incident happened")
        input_ask.set_description(".eg: `One hour ago` or `12:00 on the 24.1.2020`")
        input_ask.validator = self.no_bot_invocation_validator
        answer = await input_ask.ask()
        base_datetime = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        parsed_datetime = dateparser.parse(answer)
        parsed_datetime = parsed_datetime.replace(tzinfo=timezone.utc) if parsed_datetime is not None else parsed_datetime
        self.time = (parsed_datetime, answer)

    async def _ask_public_text_helper(self):
        input_ask = AskInput(self.author, self.channel, timeout=1500, delete_answers=True, delete_question=True, error_on=True)
        input_ask.set_title("Please input a brief text that will be publicly visible.")
        input_ask.set_description("Be carefull not to insert anything identifying.\nMax size of this text is 950 characters.\n\n***If you do not want to enter a public text, enter `None`!***")
        input_ask.validator = self.no_bot_invocation_validator
        return await input_ask.ask()

    async def _ask_public_text(self):
        answer = await self._ask_public_text_helper()

        while len(answer) > 950:
            await self.channel.send(f"__***The provide public text is too large!\nMax lenght: 950 characters\nYour text lenght: {len(answer)} characters!\n\nPlease Enter a new public text!***__", allowed_mentions=discord.AllowedMentions.none(), delete_after=120)
            answer = await self._ask_public_text_helper()
        self.public_text = answer

    async def _ask_text(self):
        input_ask = AskInputManyAnswers(self.author, self.channel, timeout=1500, delete_question=True, delete_answers=True, error_on=True)
        input_ask.set_title("Please describe the Incident. Try to be brief, but clear!")
        input_ask.set_description("**⚠️If you want to add a link, do it here,\nbut file Attachments can be added in a different question! ⚠️**")
        input_ask.validator = self.no_bot_invocation_validator
        answer = await input_ask.ask()
        self.text = answer

    async def _ask_files(self):
        file_ask = AskFile(self.author, self.channel, timeout=1500, delete_question=True, delete_answers=True, error_on=True)
        file_ask.set_title("Here you can attach files as evidence!")
        file_ask.set_description("Limited to 9 attachments!")
        answer_attachments = await file_ask.ask()
        self.files = answer_attachments

    async def summary_embed(self):
        title = "Report"
        description = "A summary of your Report"
        fields = [self.cog.bot.field_item(name="Report ID", value=self.report_id, inline=False)]
        target_value = self.target
        if self.target_type == 'discord_member':
            target_value = f"{self.target.mention} ({embed_hyperlink('Profile Link', self.user_profile_base_url+str(self.target.id))})"
        elif self.target_type == 'ingame_name':
            target_value = f"{self.target} (`ingame name`)"

        fields.append(self.cog.bot.field_item(name="Report about", value=target_value, inline=False))

        location_value = f"{self.location} (`{self.location_type.replace('_',' ').title()}`)"
        if self.location_type == "discord_channel":
            location_value = self.location.mention

        elif self.location_type == "community_server":
            location_value = f"{self.location.pretty_name} (`{self.location_type}`)"

        fields.append(self.cog.bot.field_item(name='Incident location', value=location_value, inline=False))

        time_value = f"{self.time[0].isoformat(timespec='seconds')} UTC\n`{self.time[1]}`" if self.time[0] is not None else f"`{self.time[1]}`"

        fields.append(self.cog.bot.field_item(name="Incident happend at", value=time_value, inline=False))

        report_text_value = shorten_string(self.text, 1000, shorten_side='left')
        fields.append(self.cog.bot.field_item(name="Report Text", value=report_text_value, inline=False))
        if self.files != []:
            files_value = ListMarker.make_list([file.filename for file in self.files])
            files_value = shorten_string(files_value, 1000, shorten_side='left')
            fields.append(self.cog.bot.field_item(name="Report Attachments", value=files_value, inline=False))

        fields.append(self.cog.bot.field_item(name="Public description", value=self.public_text))

        embed_data = await self.cog.bot.make_generic_embed(title=title, description=description, fields=fields, thumbnail=None, author=self.author, typus="report_internal_embed")
        if len(self.text) > 1000:
            embed_data['files'].append(await self.text_to_file())
        return embed_data

    async def text_to_file(self) -> discord.File:
        with StringIO() as string_file:
            await asyncio.to_thread(string_file.write, self.text)
            string_file.seek(0)
            current_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")

            file = discord.File(string_file, filename=f"report_{self.author.id}_{current_date}.txt")
        return file

    async def _ask_report_confirm(self):
        summary_embed = await self.summary_embed()

        summary_message = await self.channel.send(**summary_embed)
        for attachment_file in self.files:
            file = await attachment_file.to_file(spoiler=True)
            await self.channel.send(file=file, reference=summary_message.to_reference(fail_if_not_exists=False))
        confirm_ask = AskConfirmation(self.author, self.channel, timeout=600, delete_question=True, error_on=True)
        confirm_ask.set_description(f"Is the above {embed_hyperlink('Summary of your Report', summary_message.jump_url)} correct?\n **Do your really want to send this Report__(can not be canceled after this confirmation)__**?")
        answer = await confirm_ask.ask()
        if answer is confirm_ask.DECLINED:
            embed = summary_message.embeds[0]
            embed.description = f"***CANCELED***\n{embed.description}"
            await summary_message.edit(embed=embed)
        return True if answer is confirm_ask.ACCEPTED else False

    async def anonymized_report_embed(self):
        embed_data = await self.summary_embed()

        embed = embed_data['embed']
        embed.description = "Anonymized Report"
        embed.remove_author()
        for i in [4, 4]:
            embed.remove_field(i)
        embed.set_footer(text="report_public_embed")
        embed_data['embed'] = embed
        embed_data['files'] = []
        return embed_data

    async def send_random_delayed_anonymized_report(self):
        wait_seconds = random.randint(30, 180)
        await asyncio.sleep(wait_seconds)
        anonymized_embed_data = await self.anonymized_report_embed()
        await self.cog.report_channel_anonymized.send(**anonymized_embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def collect_report(self):

        await self._ask_for_target()
        await self._ask_for_location()
        await self._ask_time()
        await self._ask_text()
        await self._ask_public_text()
        await self._ask_files()

        if await self._ask_report_confirm() is True:
            summary_embed = await self.summary_embed()
            summary_message = await self.cog.report_channel_anonymized.send(**summary_embed, allowed_mentions=discord.AllowedMentions.none())
            for attachment_file in self.files:
                file = await attachment_file.to_file(spoiler=True)
                await self.cog.report_channel_anonymized.send(f"Report ID: {self.report_id}", file=file, reference=summary_message.to_reference(fail_if_not_exists=False))
            asyncio.create_task(self.send_random_delayed_anonymized_report())
        else:
            await self.channel.send("report was canceled", allowed_mentions=discord.AllowedMentions.none())


class RemarkItem:
    cog: "ReportCog" = None
    ask_text_data_file = APPDATA['remark_text_data.json']
    user_profile_base_url = "https://discordapp.com/users/"
    color_type_map = {"Positive": 'green',
                      'Neutral': 'grey',
                      'Negative': 'red'}
    type_emoji_map = {'Positive': "✅",
                      "Neutral": "❕",
                      "Negative": "❌"}
    datetime_format = "%Y-%m-%d %H-%M-%S UTC"
    template_file = Path(APPDATA['remark_template.jinja'])
    jinja_env = Environment(loader=BaseLoader, enable_async=True)

    def __init__(self, author: discord.Member, channel: discord.DMChannel):
        self.author = author
        self.channel = channel
        self.remark_id = self._determine_remark_id()
        self.remark_type = None
        self.target = None
        self.text = ""
        self.files = []
        self.full_message_data = None
        self.ask_text_data = loadjson(self.ask_text_data_file)

    def _determine_remark_id(self):
        current_date = datetime.now(tz=timezone.utc)
        id_string = current_date.isoformat() + str(self.author.id)
        id_bytes = id_string.encode('utf-8', errors='ignore')
        id_hash = shake_256(id_bytes).hexdigest(8)
        return int(id_hash, 16)

    @classmethod
    async def from_ctx(cls, ctx: commands.Context):
        author = ctx.author
        channel = ctx.channel if ctx.channel.type is discord.ChannelType.private else await cls.cog.bot.ensure_dm_channel(author)
        return cls(author=author, channel=channel)

    def no_bot_invocation_validator(self, text: str):

        for prefix in self.cog.bot.all_prefixes_for_check:
            if text.startswith(prefix):
                return False
        if text == '':
            return False
        return True

    async def _ask_for_type(self):
        ask_text_data = self.ask_text_data.get('ask_for_type', {})
        selection_ask = AskSelection(author=self.author, channel=self.channel, timeout=600, delete_question=False, error_on=True)
        selection_ask.set_title(ask_text_data.get('title'))
        selection_ask.set_description(ask_text_data.get('description').replace('\n\n\n', f"\n{ZERO_WIDTH}\n"))

        for item in ask_text_data.get('extra_fields', []):
            selection_ask.add_extra_field(name=item.get('name'), content=item.get('content', ZERO_WIDTH))
        selection_ask.options.add_option(AskSelectionOption(item="Positive", emoji=ask_text_data.get("option_positive_emoji", "✅"), description=ask_text_data.get("option_positive")))
        selection_ask.options.add_option(AskSelectionOption(item="Neutral", emoji=ask_text_data.get("option_neutral_emoji", "❕"), description=ask_text_data.get("option_neutral")))
        selection_ask.options.add_option(AskSelectionOption(item="Negative", emoji=ask_text_data.get("option_negative_emoji", "❌"), description=ask_text_data.get("option_negative")))
        main_answer = await selection_ask.ask()
        self.remark_type = main_answer

    async def _ask_for_target(self):
        ask_text_data = self.ask_text_data.get('ask_for_target', {})
        input_ask = AskInputWithEmoji(author=self.author, channel=self.channel, timeout=600, delete_question=False, delete_answers=False, error_on=True)
        input_ask.set_title(ask_text_data.get("title"))
        input_ask.set_description(ask_text_data.get("description").replace('\n\n\n', f"\n{ZERO_WIDTH}\n"))
        for item in ask_text_data.get('extra_fields', []):
            input_ask.add_extra_field(name=item.get('name'), content=item.get('content', ZERO_WIDTH))
        input_ask.validator = self.no_bot_invocation_validator
        answer = await input_ask.ask()
        maybe_target_member = None
        if '#' in answer:
            maybe_target_member = self.cog.bot.member_by_name(answer.strip())
        elif answer.isnumeric() and len(answer) == 18:
            maybe_target_member = self.cog.bot.get_antistasi_member(int(answer))
        if maybe_target_member is not None:
            self.target = maybe_target_member.mention
        else:
            self.target = f"`{answer}`"

    async def _ask_text(self):
        ask_text_data = self.ask_text_data.get('ask_text', {})
        input_ask = AskInputWithEmoji(self.author, self.channel, timeout=1500, delete_question=False, delete_answers=False, error_on=True)
        input_ask.set_title(ask_text_data.get('title'))
        input_ask.set_description(ask_text_data.get('description').replace('\n\n\n', f"\n{ZERO_WIDTH}\n"))
        for item in ask_text_data.get('extra_fields', []):
            input_ask.add_extra_field(name=item.get('name'), content=item.get('content', ZERO_WIDTH))
        input_ask.validator = self.no_bot_invocation_validator
        answer = await input_ask.ask()
        self.text = answer

    async def _ask_files(self):
        ask_text_data = self.ask_text_data.get('ask_files', {})
        file_ask = AskFileWithEmoji(self.author, self.channel, timeout=1500, delete_question=False, delete_answers=False, error_on=True)
        file_ask.set_title(ask_text_data.get('title'))
        file_ask.set_description(ask_text_data.get('description').replace('\n\n\n', f"\n{ZERO_WIDTH}\n"))
        for item in ask_text_data.get('extra_fields', []):
            file_ask.add_extra_field(name=item.get('name'), content=item.get('content', ZERO_WIDTH))
        answer_attachments = await file_ask.ask()
        self.files = answer_attachments

    async def make_full_message_data(self):

        data = {}
        data['utc_time'] = datetime.now(tz=timezone.utc).strftime(self.datetime_format)
        data['remarker'] = self.author.mention
        data['remark_type'] = self.remark_type
        data['target'] = self.target
        data['remark_text'] = self.text if len(self.text) <= 1900 else "see attachment"
        data['remark_type_emoji'] = self.type_emoji_map.get(self.remark_type)
        data['remark_id'] = self.remark_id
        template = self.jinja_env.from_string(self.template_file.read_text())
        text = await template.render_async(**data)
        files = []
        async with self.channel.typing():
            if len(self.text) > 1900:
                files.append(await self.text_to_file())
            # if len(self.files) > 2 or any(attachment.size >= 8388608 for attachment in self.files):
            #     files.append(await self.files_to_zip())

            # else:
            for attachment_file in self.files:
                files.append(await attachment_file.to_file(spoiler=False))
        return {'content': text, 'files': files, 'allowed_mentions': discord.AllowedMentions.none()}

    async def files_to_zip(self):
        def _write_zip(items):

            with BytesIO() as bytefile:
                with ZipFile(bytefile, 'w', compression=ZIP_LZMA) as zippy:
                    for _name, _data in items:
                        zippy.writestr(_name, data=_data)

                bytefile.seek(0)
                current_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S UTC")
                return discord.File(bytefile, f"remark_{self.author.id}_{current_date}.zip")
        all_items = []
        for attachment in self.files:
            name = attachment.filename
            data = await attachment.read()
            all_items.append((name, data))
        return await asyncio.to_thread(_write_zip, all_items)

    async def text_to_file(self) -> discord.File:
        with StringIO() as string_file:
            await asyncio.to_thread(string_file.write, self.text)
            string_file.seek(0)
            current_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S UTC")

            file = discord.File(string_file, filename=f"remark_{self.author.id}_{current_date}.txt")
        return file

    async def _ask_remark_confirm(self):
        self.full_message_data = await self.make_full_message_data()
        ask_text_data = self.ask_text_data.get('ask_remark_confirm', {})
        summary_message = await self.channel.send(self.full_message_data.get('content'))
        for file in self.full_message_data.get('files'):
            await self.channel.send(file=file)

        confirm_ask = AskConfirmation(self.author, self.channel, timeout=600, delete_question=False, error_on=True)
        confirm_ask.set_title(ask_text_data.get('title'))
        confirm_ask.set_description(
            f"Is the above {embed_hyperlink('Summary of your Remark', summary_message.jump_url)} correct?\n **Do your really want to send this Remark__(can not be canceled after this confirmation)__**?\n{ZERO_WIDTH}\n❎ cancels the remark, same as 🛑")
        answer = await confirm_ask.ask()
        if answer is confirm_ask.DECLINED:
            await self.channel.send("**Remark was canceled!**")
        else:
            await self.channel.send("**Your Remark has been submitted!**")
        return True if answer is confirm_ask.ACCEPTED else False

    async def collect_report(self):
        async with self.cog.bot.restart_blocker:
            await self._ask_for_type()
            await self._ask_for_target()
            await self._ask_text()
            await self._ask_files()

            if await self._ask_remark_confirm() is True:

                await self.cog.send_to_remark_webhook(await self.make_full_message_data())
            else:
                await self.channel.send("Remark was canceled", allowed_mentions=discord.AllowedMentions.none())


class ReportCog(AntiPetrosBaseCog):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.OUTDATED | CogMetaStatus.CRASHING | CogMetaStatus.EMPTY | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {"report_webhook_urls": "",
                                            "report_channel_anonymized": "bot-testing"}}
    required_folder = []
    required_files = []
    remark_emoji = "📮"

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)


# endregion [Init]

# region [Properties]


    @property
    def remark_request_channel_id(self):
        channel_id = COGS_CONFIG.retrieve(self.config_name, "remark_request_channel_id", typus=int, direct_fallback=None)
        return channel_id

    @property
    def remark_request_message_id(self):
        msg_id = COGS_CONFIG.retrieve(self.config_name, "remark_request_message_id", typus=int, direct_fallback=None)
        return msg_id

    @property
    def remark_webhook_urls(self):
        return COGS_CONFIG.retrieve(self.config_name, "remark_webhook_urls", typus=List[str], direct_fallback=["https://discord.com/api/webhooks/854749192189640734/kd3tmI17bErnc6egy8ObrdfV6-Rm79hkPxNFxBjeZDSp4wNv4llJ8EG-9_z_6Awv8Jeu"])

    @property
    def report_webhook_urls(self):
        return COGS_CONFIG.retrieve(self.config_name, "report_webhook_urls", typus=List[str], direct_fallback=[])

    @property
    def report_channel_anonymized(self):
        channel = COGS_CONFIG.retrieve(self.config_name, "report_channel_anonymized", typus=str, direct_fallback="bot-testing")
        if channel.isnumeric():
            return self.bot.channel_from_id(int(channel))
        else:
            return self.bot.channel_from_name(channel)

    @property
    def possible_servers(self):
        community_server_info_cog = self.bot.get_cog("CommunityServerInfoCog")
        return community_server_info_cog.server_items


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await super().on_ready_setup()
        RemarkItem.cog = self
        ReportItem.cog = self
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus)
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @ commands.Cog.listener(name='on_raw_reaction_add')
    async def remark_on_emoji_listener(self, payload: discord.RawReactionActionEvent):
        if self.completely_ready is False:
            return
        if self.remark_request_channel_id is None or self.remark_request_message_id is None:
            return
        if payload.channel_id != self.remark_request_channel_id:
            return
        if payload.message_id != self.remark_request_message_id:
            return
        reaction_member = payload.member if payload.member is not None else self.bot.get_antistasi_member(payload.user_id)

        if reaction_member.bot is True:
            return
        try:
            message = await self.bot.get_message_directly(payload.channel_id, payload.message_id)

        except discord.errors.NotFound:
            return
        emoji = str(payload.emoji)
        await message.remove_reaction(payload.emoji, reaction_member)
        if emoji == str(self.remark_emoji):

            try:
                remark = RemarkItem(author=reaction_member, channel=await self.bot.ensure_dm_channel(reaction_member))
                await remark.collect_report()
            except BaseException as e:
                log.exception("encountered exception", exc_info=e)

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(clear_invocation=True)
    @owner_or_admin()
    async def make_remark_emoji_message(self, ctx: commands.Context, remark_channel: discord.TextChannel):
        current_message = await self.get_remark_request_message()
        if current_message is not None:
            await current_message.delete()
        description = f'To make a Remark, please react to this message with {self.remark_emoji}, then you will be contacted per DM by the Bot.'
        title = 'REMARK SYSTEM'
        if self.bot.is_debug is True:
            description = f"⚠️⚠️ **THIS IS JUST A TEST** ⚠️⚠️\n{ZERO_WIDTH}\n‼️ **__DO NOT__** SEND REAL REMARKS WITH THIS.\n‼️ You can use real users, but **make up a stupid story**\n‼️ most of all ***TRY TO BREAK IT***\n" + ZERO_WIDTH + '\n' + description
            title = title + ' TEST'

        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=description,
                                                       thumbnail="https://www.lotus-qa.com/wp-content/uploads/2020/02/testing.jpg",
                                                       timestamp=None,
                                                       fields=[self.bot.field_item('If something goes wrong:', 'Please contact an Admin and tell im the situation, they will then contact `Giddi`, to fix the bug!')])
        msg = await remark_channel.send(**embed_data)
        await msg.add_reaction(self.remark_emoji)
        COGS_CONFIG.set(self.config_name, 'remark_request_channel_id', str(remark_channel.id))
        COGS_CONFIG.set(self.config_name, 'remark_request_message_id', str(msg.id))

    @auto_meta_info_command()
    async def remark(self, ctx: commands.Context):
        remark = await RemarkItem.from_ctx(ctx)

        await delete_message_if_text_channel(ctx)
        try:
            await remark.collect_report()
        except BaseException as e:
            log.exception("encountered exception", exc_info=e)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def report(self, ctx: commands.Context):
        if self.bot.is_debug is True:
            log.info("Report started by Member %s", ctx.author)
        report = await ReportItem.from_ctx(ctx)
        await delete_message_if_text_channel(ctx)
        await report.collect_report()

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    async def send_to_remark_webhook(self, remark_data):
        for webhook_url in self.remark_webhook_urls:
            webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(self.bot.aio_session))
            _remark_data = {'allowed_mentions': discord.AllowedMentions.none()} | remark_data
            await webhook.send(**_remark_data)

    async def get_remark_request_message(self) -> discord.Message:
        channel_id = self.remark_request_channel_id
        msg_id = self.remark_request_message_id
        if msg_id is None or channel_id is None:
            return None
        try:
            msg = await self.bot.get_message_directly(channel_id, msg_id)
            return msg
        except discord.NotFound:
            return None

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
    bot.add_cog(ReportCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
