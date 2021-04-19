# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
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
from io import BytesIO
from textwrap import dedent
from typing import Optional, Union, Any, TYPE_CHECKING, Callable, Iterable, List, Dict, Set, Tuple, Mapping
from inspect import isclass
# * Third Party Imports -->
from icecream import ic
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property
from dateparser import parse as date_parse

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, delete_message_if_text_channel, async_write_json, async_load_json, split_camel_case_string
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker, AllowedChannelAndAllowedRoleCheck, BaseAntiPetrosCheck
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled, writeit, readit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker, Seperators, SPECIAL_SPACE
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState, UpdateTypus, CommandCategory
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCommand, AntiPetrosFlagCommand, AntiPetrosBaseGroup, auto_meta_info_group
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.converters import FlagArg, CogConverter, CheckConverter, CommandConverter, DateOnlyConverter, LanguageConverter, DateTimeFullConverter, date_time_full_converter_flags, CategoryConverter
from antipetros_discordbot.utility.exceptions import ParameterError

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

COG_NAME = "HelpCog"

CONFIG_NAME = "help_settings"

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)


def no_filter(in_object):
    return True


def no_name_modifier(in_name: str) -> str:
    return in_name


def filter_with_user_role(owner_ids: List[int], in_member: discord.Member, only_working: bool = True, only_enabled: bool = True):
    role_names = ['all'] + [role.name.casefold() for role in in_member.roles]

    def actual_filter(in_object):

        if isinstance(in_object, (AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand)):
            if in_member.id in owner_ids:
                return True
            allowed_roles = [c_role.casefold() for c_role in in_object.allowed_roles]
            return any(role in allowed_roles for role in role_names)
        elif isinstance(in_object, commands.Cog):
            if only_enabled is True and in_object.enabled is False:
                return False
            if in_member.id in owner_ids:
                return True
            if only_working is True and CogState.WORKING not in in_object.docattrs.get("is_ready"):
                return False
            if in_object.docattrs.get('show_in_readme') is False:
                return any(role in ['admin', 'admin lead'] for role in role_names)
            else:
                return True
        elif isinstance(in_object, CommandCategory):
            return in_object.visibility_check(role_names)
    return actual_filter

# endregion [Helper]


class HelpCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    WiP
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': False,
                'is_ready': CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,
                'extra_description': dedent("""
                                            """).strip(),
                'caveat': None}

    required_config_data = dedent("""
                                    """).strip('\n')
    data_folder = pathmaker(APPDATA['documentation'], 'help_data')
    general_help_description_file = pathmaker(data_folder, 'general_help_description.md')
    emoji_strings = {'commands': f'{ZERO_WIDTH}'.join(["🇨", "🇴", "🇲", "🇲", "🇦", "🇳", "🇩", "🇸"]),
                     "description": f'{ZERO_WIDTH}'.join(["🇩", "🇪", "🇸", "🇨", "🇷", "🇮", "🇵", "🇹", "🇮", "🇴", "🇳"])}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.help_dispatch_map = {commands.Cog: self._send_cog_help,
                                  AntiPetrosBaseCommand: self._send_command_help,
                                  AntiPetrosBaseGroup: self._send_command_help,
                                  AntiPetrosFlagCommand: self._send_command_help,
                                  CommandCategory: self._send_toolbox_help,
                                  BaseAntiPetrosCheck: self._send_check_help}
        glog.class_init_notification(log, self)


# endregion [Init]

# region [Properties]


    @property
    def general_help_description(self):
        if os.path.isfile(self.general_help_description_file) is False:
            writeit(self.general_help_description_file, 'WiP')
        from_config = BASE_CONFIG.retrieve(self.config_name, 'general_description', typus=str, direct_fallback='-file-')
        if from_config.casefold() == '-file-':
            return readit(self.general_help_description_file)
        return from_config


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command(enabled=True, categories=[CommandCategory.META])
    async def help(self, ctx: commands.Context, in_object: Optional[Union[CommandConverter, CogConverter, CategoryConverter, CheckConverter]]):
        raw_params = ctx.message.content.split(ctx.invoked_with)[-1].strip()

        if in_object is None and raw_params == '':
            await self._send_overall_help(ctx)

        elif in_object is None and raw_params != '':
            raise ParameterError('in_object', raw_params)
        else:
            await self._get_dispatcher(in_object)(ctx, in_object)

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def _send_overall_help(self, ctx: commands.Context):
        member_filter = filter_with_user_role(self.bot.owner_ids, await self.bot.retrieve_antistasi_member(ctx.author.id), True)
        cogs = await self.all_cogs(member_filter, self.remove_cog_suffix_cog_name_modifier)
        log.debug('preparing help embed')
        fields = []
        for cog_name, cog in cogs.items():
            if cog_name.casefold() != "generaldebug":
                value_text = f"> *{cog.description}*\n{SPECIAL_SPACE*4}{ListMarker.circle_star} **Commands:**\n"
                command_names = [f"`{command.name}` ☑️" if command.enabled is True else f"`{command.name}` ❎" for command in cog.get_commands() if member_filter(command) is True]
                command_names.sort()
                value_text += '\n'.join(f"{SPECIAL_SPACE*16}{ListMarker.triangle} {command_name}" for command_name in command_names)
                value_text += f'\n{ZERO_WIDTH}'
                fields.append(self.bot.field_item(name=f"{ListMarker.bullet} {split_camel_case_string(cog_name).title()}", value=value_text))

        fields.append(self.bot.field_item(name=f"{ListMarker.bullet} Command Tool Sets", value=f'{ZERO_WIDTH}\n' + '\n'.join(f"{SPECIAL_SPACE*8}{ListMarker.circle_star} *{category}*" for category in await self.all_categories(member_filter))))
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title='General Help', description=self.general_help_description,
                                                                            fields=fields,
                                                                            thumbnail='help',
                                                                            color="GIDDIS_FAVOURITE",
                                                                            timestamp=None):
            await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def _send_cog_help(self, ctx: commands.Context, cog: commands.Cog):
        await ctx.send('cog')

    async def _send_command_help(self, ctx: commands.Context, command: Union[AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand]):
        await ctx.send('command')

    async def _send_toolbox_help(self, ctx: commands.Context, toolbox_category: CommandCategory):
        await ctx.send('toolbox')

    async def _send_check_help(self, ctx: commands.Context, check: BaseAntiPetrosCheck):
        await ctx.send('check')

    async def all_cogs(self, cog_filter: Callable = no_filter, cog_name_modifier: Callable = no_name_modifier):
        _out = {}
        for cog_name, cog in self.bot.cogs.items():
            if cog_filter(cog) is True:
                _out[cog_name_modifier(cog_name)] = cog
        return _out

    async def all_categories(self, category_filter: Callable = no_filter, category_name_modifier: Callable = no_name_modifier):
        _out = {}
        for category_name, category_member in CommandCategory.__members__.items():

            if category_filter(category_member) is True:
                _out[category_name_modifier(category_name)] = category_member
        return _out

    @staticmethod
    def not_hidden_working_cog_filter(cog: commands.Cog):
        if cog.docattrs.get('show_in_readme') is False:
            return False
        if CogState.WORKING not in cog.docattrs.get('is_ready'):
            return False
        return True

    @staticmethod
    def remove_cog_suffix_cog_name_modifier(cog_name: str):
        return cog_name.removesuffix('Cog')

    def _get_dispatcher(self, in_object):
        for key, value in self.help_dispatch_map.items():
            if isclass(in_object):
                if issubclass(in_object, key):
                    return value
            else:
                if isinstance(in_object, key):
                    return value
        raise ParameterError('in_object', in_object)

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

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(HelpCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
