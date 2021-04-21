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
from functools import wraps, lru_cache, singledispatch, total_ordering, partial, cached_property
from contextlib import contextmanager, asynccontextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from multiprocessing import Pool
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
import unicodedata
from io import BytesIO
from textwrap import dedent, indent, TextWrapper
import imgkit
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
from fuzzywuzzy import fuzz, process as fuzzprocess
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property
from dateparser import parse as date_parse
from inspect import getmembers, getdoc, getsource, getsourcefile, getsourcelines, getframeinfo, getfile
# * Gid Imports -->
import gidlogger as glog
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
# * Local Imports -->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even, alt_seconds_to_pretty, delete_message_if_text_channel, antipetros_repo_rel_path
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled, bytes2human, readit, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH


from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock, html_codeblock
from antipetros_discordbot.utility.converters import CommandConverter
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle

from typing import TYPE_CHECKING, Any, Union, Optional, Callable, Iterable, List, Dict, Set, Tuple, Mapping, Coroutine, Awaitable
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus, CommandCategory
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

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


class CodeHighlighStyle(Enum):
    DRACULA = DraculaStyle
    TOMORROW = TomorrowStyle
    TOMORROWNIGHT = TomorrownightStyle
    TOMORROWNIGHTBLUE = TomorrownightblueStyle
    TOMORROWNIGHTBRIGHT = TomorrownightbrightStyle
    TOMORROWNIGHTEIGHTIES = TomorrownighteightiesStyle


class InfoCog(AntiPetrosBaseCog):
    """
    WiP
    """
# region [ClassAttributes]

    public = True
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

    antistasi_guild_id = 449481990513754112
    code_style_map = {'dracula': DraculaStyle,
                      'tomorrow': TomorrowStyle,
                      'tomorrownight': TomorrownightStyle,
                      'tomorrownightbright': TomorrownightbrightStyle,
                      'tomorrownightblue': TomorrownightblueStyle,
                      'tomorrownighteighties': TomorrownighteightiesStyle} | {name.casefold(): get_style_by_name(name) for name in get_all_styles()}

# endregion [ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.ready = False
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def uptime(self):
        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        return alt_seconds_to_pretty(seconds)

    @cached_property
    @universal_log_profiler
    def join_rankdict(self):
        all_members_and_date = [(member, member.joined_at) for member in self.bot.antistasi_guild.members]
        all_members_sorted = sorted(all_members_and_date, key=lambda x: x[1])
        return {member_data[0]: join_index + 1 for join_index, member_data in enumerate(all_members_sorted)}

    @property
    @universal_log_profiler
    def code_style(self):
        style_name = COGS_CONFIG.retrieve(self.config_name, 'code_style', typus=str, direct_fallback='dracula')
        style = self.code_style_map.get(style_name.casefold())
        if style is None:
            raise KeyError(f'no such style as {style_name}')
        return style

# endregion [Properties]

# region [Setup]
    @universal_log_profiler
    async def on_ready_setup(self):
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_bot(self, ctx: commands.Context):
        name = self.bot.display_name
        cleaned_prefixes = await self._clean_bot_prefixes(ctx)

        data = {"Usable Prefixes": ('\n'.join(cleaned_prefixes), False),
                "Commands are Case-INsensitive?": ('✅' if self.bot.case_insensitive is True else '❎', True),
                "Number of Commands": (await self.amount_commands(), True),
                "Release Date": (datetime(year=2021, month=3, day=11).strftime("%a the %d. of %b, %Y"), True),
                "Version": (str(os.getenv('ANTIPETROS_VERSION')), True),
                "Uptime": (self.uptime, True),
                "Current Latency": (f"{round(self.bot.latency * 1000)} ms", True),
                "Created By": (self.bot.creator.member_object.mention, True),
                "Github Link": (embed_hyperlink('Github Repo', self.bot.github_url), True),
                "Wiki": (embed_hyperlink('Github Wiki', self.bot.wiki_url), True),
                "Invocations since launch": (await self.bot.get_amount_invoked_overall(), True),
                "Roles": (', '.join(role.mention for role in self.bot.all_bot_roles if "everybody" not in role.name.casefold()), False),
                }

        fields = []
        for key, value in data.items():
            if value[0] not in ['', None]:
                fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
        embed_data = await self.bot.make_generic_embed(title=name,
                                                       description=self.bot.description,
                                                       image=self.bot.portrait_url,
                                                       url=self.bot.github_url,
                                                       fields=fields,
                                                       thumbnail=None)
        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_guild(self, ctx: commands.Context):
        """
        Shows some attributes of the current Guild.
        """
        as_guild = self.bot.antistasi_guild
        # await as_guild.chunk()
        thumbnail = None
        image = str(as_guild.banner_url)
        description = as_guild.description
        if description is None:
            description = "This Guild has no description set"

        data = {'Amount of Channels overall': (len([channel for channel in as_guild.channels if channel.type is not discord.ChannelType.category and not channel.name.casefold().startswith('ticket-')]), True),
                'Amount of Text Channels': (len([channel for channel in as_guild.text_channels if channel.type is not discord.ChannelType.category and not channel.name.casefold().startswith('ticket-')]), True),
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
            if value[0] not in ['', None]:
                fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))

        embed_data = await self.bot.make_generic_embed(title=as_guild.name, url="https://antistasi.de/", description=description, thumbnail=thumbnail, fields=fields, image=image)
        info_msg = await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_me(self, ctx: commands.Context):
        async with ctx.typing():
            member = ctx.author
            all_true_permissions = [str(permission) for permission, value in iter(member.guild_permissions) if value is True]
            permissions = "```css\n" + ', '.join(sorted(all_true_permissions)) + '\n```'
            devices = []
            if member.mobile_status not in [discord.Status.offline, discord.Status.invisible]:
                devices.append('📱 Mobile')
            if member.desktop_status not in [discord.Status.offline, discord.Status.invisible]:
                devices.append('🖥️ Desktop')
            if member.web_status not in [discord.Status.offline, discord.Status.invisible]:
                devices.append('🌐 Web')

            data = {'Id': (f"`{member.id}`", True),
                    'Activity': (str(member.activity), False),
                    'Status': (member.raw_status, True),
                    "Device": ('\n'.join(devices), True),
                    'Roles': ('\n'.join(role.mention for role in sorted(member.roles, key=lambda x: x.position, reverse=True) if "everyone" not in role.name.casefold()), False),
                    'Account Created': (member.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), True),
                    'Joined Antistasi Guild': (member.joined_at.strftime("%H:%M:%S on %a the %Y.%b.%d"), True),
                    'Join Position': (self.join_rankdict.get(member), True),
                    'Permissions': (permissions, False)}
            fields = []

            for key, value in data.items():
                if value[0] not in ['', None]:
                    fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name, description=f"The one and only {member.mention}", thumbnail=str(member.avatar_url), fields=fields, color=member.color)
            await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(hidden=True, categories=CommandCategory.ADMINTOOLS)
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
                if value[0] not in ['', None]:
                    fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name, description=f"The one and only {member.mention}", thumbnail=str(member.avatar_url), fields=fields, color=member.color)

            await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    async def info_command(self, ctx: commands.Context, command: CommandConverter, as_codeblock: str = None):
        name = command.name
        aliases = command.aliases
        command_help = command.help
        cog_file_name = os.path.basename(await antipetros_repo_rel_path(getsourcefile(command.cog.__class__)))
        github_link, start_line_number = await self._get_github_line_link(command)
        if as_codeblock is not None and as_codeblock.casefold() == 'codeblock':
            embed_data = embed_data = await self.bot.make_generic_embed(title=name, url=github_link, description=command_help,
                                                                        fields=[self.bot.field_item(name="Aliases", value='\n'.join(aliases), inline=False),
                                                                                self.bot.field_item(name="Link to Source", value=embed_hyperlink(f"{cog_file_name}", github_link), inline=False)],
                                                                        thumbnail=None)
            rel_path = await antipetros_repo_rel_path(getsourcefile(command.cog.__class__))
            raw_source_code = f'\t# {rel_path}\n\n' + getsource(command.callback)
            await self.bot.split_to_messages(ctx, raw_source_code, in_codeblock=True, syntax_highlighting='py')
            await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        else:
            async with self._make_source_code_image(command, start_line_number) as source_image_binary:
                embed_data = await self.bot.make_generic_embed(title=name, url=github_link, description=command_help,
                                                               fields=[self.bot.field_item(name="Aliases", value='\n'.join(aliases)if aliases != [] else 'None', inline=False),
                                                                       self.bot.field_item(name="Link to Source", value=embed_hyperlink(f"{cog_file_name}", github_link), inline=False)],
                                                               thumbnail=None,
                                                               image=discord.File(source_image_binary, filename=command.name + '.png'))

                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
                gif = await self._get_command_gif(command.name)
                if gif is not None:
                    gif_file = discord.File(gif)
                    await ctx.send(file=gif_file)
                await asyncio.sleep(2)

    @auto_meta_info_command()
    @has_attachments(1)
    async def code_file_to_image(self, ctx: commands.Context, as_codeblock: str = None):
        async with ctx.typing():
            file = ctx.message.attachments[0]
            file_name = file.filename

            with TemporaryDirectory() as tempdir:
                path = pathmaker(tempdir, file_name)
                await file.save(path)
                content = readit(path)
            if as_codeblock is not None and as_codeblock.casefold() == 'codeblock':
                await self.bot.split_to_messages(ctx, content, in_codeblock=True, syntax_highlighting=file_name.split('.')[-1])
            else:
                image, lexer = await self._make_other_source_code_images(content)
                embed_data = await self.bot.make_generic_embed(title=file_name.title(),
                                                               description=f"Lexer name: `{lexer.name}`",
                                                               thumbnail=None,
                                                               image=image)
                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())


# endregion [Commands]

# region [HelperMethods]

    @universal_log_profiler
    async def _get_command_gif(self, command_name):
        gif_name = f"{command_name}_command.gif"
        for file in os.scandir(APPDATA['gifs']):
            if file.is_file() and file.name.casefold() == gif_name.casefold():
                return file.path
        return None

    @universal_log_profiler
    async def _make_other_source_code_images(self, scode: str):

        lexer = guess_lexer(scode)

        image = highlight(scode, lexer, ImageFormatter(style=self.code_style,
                                                       font_name='Fira Code',
                                                       line_number_bg="#2f3136",
                                                       line_number_fg="#ffffff",
                                                       line_number_chars=3,
                                                       line_pad=5,
                                                       font_size=20,
                                                       line_number_bold=True))

        return image, lexer

    @ asynccontextmanager
    async def _make_source_code_image(self, command: commands.Command, start_line_number: int):
        rel_path = await antipetros_repo_rel_path(getsourcefile(command.cog.__class__))
        raw_source_code = f'\t# {rel_path}\n\n' + getsource(command.callback)

        image = await asyncio.to_thread(highlight, raw_source_code, PythonLexer(), ImageFormatter(style=self.code_style,
                                                                                                  font_name='Fira Code',
                                                                                                  line_number_start=start_line_number,
                                                                                                  line_number_bg="#2f3136",
                                                                                                  line_number_fg="#ffffff",
                                                                                                  line_number_chars=3,
                                                                                                  line_pad=5,
                                                                                                  font_size=20,
                                                                                                  line_number_bold=True))
        with BytesIO() as image_binary:
            image_binary.write(image)
            image_binary.seek(0)
            yield image_binary

    @universal_log_profiler
    async def _get_github_line_link(self, command: commands.Command):
        base_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/blob/development/"
        rel_path = await antipetros_repo_rel_path(getsourcefile(command.cog.__class__))
        source_lines = getsourcelines(command.callback)
        start_line_number = source_lines[1]
        code_length = len(source_lines[0])
        full_path = base_url + rel_path + f'#L{start_line_number}-L{start_line_number+code_length-1}'
        return full_path, start_line_number

    @universal_log_profiler
    async def _get_allowed_channels(self):
        indicator_permissions = ['read_messages', 'send_messages', 'manage_messages', 'add_reactions']
        allowed_channels = []
        for channel in self.bot.antistasi_guild.text_channels:
            if channel.type is not discord.ChannelType.category:
                channel_permission = channel.permissions_for(self.bot.bot_member)
                if all(getattr(channel_permission, permission_name) is True for permission_name in indicator_permissions):
                    allowed_channels.append(channel)
        return [channel.mention for channel in sorted(allowed_channels, key=lambda x: x.position, reverse=False)]

    @universal_log_profiler
    async def _clean_bot_prefixes(self, ctx: commands.Context):
        raw_prefixes = await self.bot.get_prefix(ctx.message)
        cleaned_prefixes = list(set(map(lambda x: x.strip(), raw_prefixes)))
        cleaned_prefixes = [f"`{prefix}`" if not prefix.startswith('<') else prefix for prefix in cleaned_prefixes if '804194400611729459' not in prefix]
        return sorted(cleaned_prefixes, key=lambda x: x.startswith('<'), reverse=True)

    @universal_log_profiler
    async def _oldest_youngest_member(self, get_oldest=True):
        all_members_and_date = [(member, member.joined_at) for member in self.bot.antistasi_guild.members if member is not self.bot.antistasi_guild.owner]
        oldest_member_and_date = await self.bot.execute_in_thread(partial(sorted, all_members_and_date, key=lambda x: x[1]))
        if get_oldest is True:
            oldest_member_and_date = oldest_member_and_date[0]
        else:
            oldest_member_and_date = oldest_member_and_date[-1]
        return f'{oldest_member_and_date[0].mention} -> {oldest_member_and_date[0].name}, joined at {oldest_member_and_date[1].strftime("%H:%M:%S on %a the %Y.%b.%d")}'

    @universal_log_profiler
    async def most_used_channel(self):
        stats = await self.bot.get_usage_stats('all')
        channel, amount = stats[0]
        return f"{channel.mention} recorded usages: {amount}"

    @universal_log_profiler
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
    bot.add_cog(InfoCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
