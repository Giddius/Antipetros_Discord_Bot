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
from typing import Union, TYPE_CHECKING
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial, cached_property
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
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, alt_seconds_to_pretty, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file

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

COG_NAME = "InfoCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class InfoCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    WiP
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    antistasi_guild_id = 449481990513754112
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,)}

    required_config_data = dedent("""
                                    """).strip('\n')
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def uptime(self):
        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        return alt_seconds_to_pretty(seconds)

    @cached_property
    def join_rankdict(self):
        all_members_and_date = [(member, member.joined_at) for member in self.bot.antistasi_guild.members]
        all_members_sorted = sorted(all_members_and_date, key=lambda x: x[1])
        return {member_data[0]: join_index + 1 for join_index, member_data in enumerate(all_members_sorted)}

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(enabled=get_command_enabled('info_bot'))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    async def info_bot(self, ctx: commands.Context):
        name = self.bot.display_name
        cleaned_prefixes = await self._clean_bot_prefixes(ctx)

        data = {"Usable Prefixes": ('\n'.join(cleaned_prefixes), False),
                "Commands are Case-INsensitive?": ('✅' if self.bot.case_insensitive is True else '❎', True),
                "Number of Commands": (await self.amount_commands(), True),
                "Release Date": (datetime(year=2021, month=3, day=11).strftime("%a the %d. of %b, %Y"), True),
                "Version": (str(os.getenv('ANTIPETROS_VERSION')), True),
                "Uptime": (self.uptime, True),
                "Current Latency": (f"{round(self.bot.latency * 1000)} s", True),
                "Created By": (self.bot.creator.member_object.mention, True),
                "Github Link": (embed_hyperlink('Github Repo', self.bot.github_url), True),
                "Wiki": (embed_hyperlink('Github Wiki', self.bot.wiki_url), True),
                "Invocations since launch": (await self.bot.get_amount_invoked_overall(), True),
                "Roles": (', '.join(role.mention for role in self.bot.all_bot_roles if "everybody" not in role.name.casefold()), False),
                }

        fields = []
        for key, value in data.items():
            fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
        embed_data = await self.bot.make_generic_embed(title=name,
                                                       description=self.bot.description,
                                                       image=self.bot.portrait_url,
                                                       url=self.bot.github_url,
                                                       fields=fields,
                                                       thumbnail=None)
        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(enabled=get_command_enabled('info_guild'))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    async def info_guild(self, ctx: commands.Context):
        as_guild = self.bot.antistasi_guild
        # await as_guild.chunk()
        thumbnail = None
        image = str(as_guild.banner_url)
        description = as_guild.description
        if description is None:
            description = "This Guild has no description set"

        data = {'Amount of Channels overall': (len([channel for channel in as_guild.channels if channel.type is not discord.ChannelType.category]), True),
                'Amount of Text Channels': (len(as_guild.text_channels), True),
                'Amount of Voice Channels': (len(as_guild.voice_channels), True),
                "Amount Members": (len(as_guild.members), True),
                'Amount Custom Emojis': (len(as_guild.emojis), True),
                "Amount Roles": (len(as_guild.roles), True),
                "Current Premium Tier": (as_guild.premium_tier, True),
                "Current Boosts": (as_guild.premium_subscription_count, True),
                'Current File Size Limit': (bytes2human(as_guild.filesize_limit, annotate=True), True),
                "Preferred Locale": (as_guild.preferred_locale, True),
                'Created at': (as_guild.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), False),
                "Owner": (f"{as_guild.owner.mention} -> {as_guild.owner.name}", False),
                "Current Booster": ('\n'.join(f"{member.mention} -> {member.name}" for member in as_guild.premium_subscribers), False),
                "Rules Channel": (as_guild.rules_channel.mention, False),
                "Member for longest time": (await self._oldest_youngest_member(True), False),
                "Member for shortest time": (await self._oldest_youngest_member(False), False),
                "Most Used Channel since bot went live": (await self.most_used_channel(), False)}

        fields = []
        for key, value in data.items():
            fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))

        embed_data = await self.bot.make_generic_embed(title=as_guild.name, url="https://antistasi.de/", description=description, thumbnail=thumbnail, fields=fields, image=image)
        info_msg = await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(enabled=get_command_enabled('info_me'))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    async def info_me(self, ctx: commands.Context):
        async with ctx.typing():
            member = ctx.author
            all_true_permissions = [str(permission) for permission, value in iter(member.guild_permissions) if value is True]
            permissions = "```css\n" + ', '.join(sorted(all_true_permissions)) + '\n```'

            data = {'Id': (f"`{member.id}`", True),
                    'Activity': (str(member.activity), False),
                    'Status': (member.raw_status, True),
                    "Device": ('🖥️ Desktop' if member.is_on_mobile() is False else '📱 Mobile', True),
                    'Roles': ('\n'.join(role.mention for role in sorted(member.roles, key=lambda x: x.position, reverse=True) if "everyone" not in role.name.casefold()), False),
                    'Account Created': (member.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), True),
                    'Joined Antistasi Guild': (member.joined_at.strftime("%H:%M:%S on %a the %Y.%b.%d"), True),
                    'Join Position': (self.join_rankdict.get(member), True),
                    'Permissions': (permissions, False)}
            fields = []
            for key, value in data.items():
                fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name, description=f"The one and only {member.mention}", thumbnail=str(member.avatar_url), fields=fields, color=member.color)
            await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(enabled=get_command_enabled('info_me'))
    @owner_or_admin(False)
    async def info_other(self, ctx: commands.Context, member_id: int):
        async with ctx.typing():
            member = await self.bot.retrieve_antistasi_member(member_id)
            all_true_permissions = [str(permission) for permission, value in iter(member.guild_permissions) if value is True]
            permissions = "```css\n" + ', '.join(sorted(all_true_permissions)) + '\n```'
            data = {'Id': (f"`{member.id}`", True),
                    'Activity': (str(member.activity), False),
                    'Status': (member.raw_status, True),
                    "Device": ('🖥️ Desktop' if member.is_on_mobile() is False else '📱 Mobile', True),
                    'Roles': ('\n'.join(role.mention for role in sorted(member.roles, key=lambda x: x.position, reverse=True) if "everyone" not in role.name.casefold()), False),
                    'Account Created': (member.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), True),
                    'Joined Antistasi Guild': (member.joined_at.strftime("%H:%M:%S on %a the %Y.%b.%d"), True),
                    'Join Position': (self.join_rankdict.get(member), True),
                    'Permissions': (permissions, False)}
            fields = []
            for key, value in data.items():
                fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name, description=f"The one and only {member.mention}", thumbnail=str(member.avatar_url), fields=fields, color=member.color)

            await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def _get_allowed_channels(self):
        indicator_permissions = ['read_messages', 'send_messages', 'manage_messages', 'add_reactions']
        allowed_channels = []
        for channel in self.bot.antistasi_guild.text_channels:
            if channel.type is not discord.ChannelType.category:
                channel_permission = channel.permissions_for(self.bot.bot_member)
                if all(getattr(channel_permission, permission_name) is True for permission_name in indicator_permissions):
                    allowed_channels.append(channel)
        return [channel.mention for channel in sorted(allowed_channels, key=lambda x: x.position, reverse=False)]

    async def _clean_bot_prefixes(self, ctx: commands.Context):
        raw_prefixes = await self.bot.get_prefix(ctx.message)
        cleaned_prefixes = list(set(map(lambda x: x.strip(), raw_prefixes)))
        cleaned_prefixes = [f"`{prefix}`" if not prefix.startswith('<') else prefix for prefix in cleaned_prefixes if '804194400611729459' not in prefix]
        return sorted(cleaned_prefixes, key=lambda x: x.startswith('<'), reverse=True)

    async def _oldest_youngest_member(self, get_oldest=True):
        all_members_and_date = [(member, member.joined_at) for member in self.bot.antistasi_guild.members if member is not self.bot.antistasi_guild.owner]
        oldest_member_and_date = await self.bot.execute_in_thread(partial(sorted, all_members_and_date, key=lambda x: x[1]))
        if get_oldest is True:
            oldest_member_and_date = oldest_member_and_date[0]
        else:
            oldest_member_and_date = oldest_member_and_date[-1]
        return f'{oldest_member_and_date[0].mention} -> {oldest_member_and_date[0].name}, joined at {oldest_member_and_date[1].strftime("%H:%M:%S on %a the %Y.%b.%d")}'

    async def most_used_channel(self):
        stats = self.bot.channel_usage_stats.get('overall')
        channel, amount = sorted(list(stats.items()), key=lambda x: x[1], reverse=True)[0]
        channel = await self.bot.channel_from_name(channel)
        return f"{channel.mention} recorded usages: {amount}"

    async def amount_commands(self, with_hidden: bool = False):
        all_commands = self.bot.commands
        if with_hidden is False:
            return len([command for command in all_commands if command.hidden is False])
        else:
            return len(all_commands)

# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx):
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
    bot.add_cog(attribute_checker(InfoCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]