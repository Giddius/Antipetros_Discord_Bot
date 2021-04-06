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
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager, asynccontextmanager
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

# * Third Party Imports -->
from icecream import ic
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
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
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, CogConfigReadOnly, make_config_name, is_even
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle
from github import Github

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

COG_NAME = "GithubCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class GithubCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    WiP
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    antistasi_repo_url = "https://github.com/official-antistasi-community/A3-Antistasi"
    antistasi_base_file_url = "https://github.com/official-antistasi-community/A3-Antistasi/blob/"
    antistasi_repo_identifier = "official-antistasi-community/A3-Antistasi"
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,)}

    required_config_data = dedent("""
                                    """).strip('\n')
    code_style_map = {'dracula': DraculaStyle,
                      'tomorrow': TomorrowStyle,
                      'tomorrownight': TomorrownightStyle,
                      'tomorrownightbright': TomorrownightbrightStyle,
                      'tomorrownightblue': TomorrownightblueStyle,
                      'tomorrownighteighties': TomorrownighteightiesStyle} | {name.casefold(): get_style_by_name(name) for name in get_all_styles()}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.github_access = Github(os.getenv('GITHUB_TOKEN'))
        self.antistasi_repo = self.github_access.get_repo(self.antistasi_repo_identifier)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def branches(self):
        return [branch.name for branch in self.antistasi_repo.get_branches()]

    @property
    def code_style(self):
        style_name = COGS_CONFIG.retrieve(self.config_name, 'code_style', typus=str, direct_fallback='dracula')
        style = self.code_style_map.get(style_name.casefold())
        if style is None:
            raise KeyError(f'no such style as {style_name}')
        return style

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

    @auto_meta_info_command()
    async def get_file(self, ctx: commands.Context, file_name: str, branch: str = None):
        async with ctx.typing():
            found_file = None
            branch = 'unstable' if branch is None else branch
            async for file in self.all_repo_files(branch_name=branch):
                if file.name.casefold() == file_name.casefold():
                    found_file = file
                    content = await self.download_to_string(file)
                    break
            if found_file is None:
                await ctx.send(f"no file named `{file_name}` in branch `{branch}`")
                return
            async with self._make_other_source_code_images(content) as source_image_binary:

                embed_data = await self.bot.make_generic_embed(title=file_name,
                                                               url=found_file.html_url,
                                                               description=embed_hyperlink("link to file", found_file.html_url),
                                                               image=discord.File(source_image_binary, filename=file_name.split(".")[0] + '.png'))
                with StringIO() as content_file:
                    content_file.write(content)
                    content_file.seek(0)
                    file = discord.File(content_file, file_name)
                    await ctx.send(file=file)
                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role_2()
    async def github_referals(self, ctx: commands.Context):
        fields = []
        for referal in self.antistasi_repo.get_top_referrers():
            fields.append(self.bot.field_item(name=referal.referrer, value=f"Amount: {referal.count}\nUnique: {referal.uniques}", inline=False))
        embed_data = await self.bot.make_generic_embed(title="Referals to the Antistasi Repo", fields=fields, url=self.antistasi_repo_url)
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role_2()
    async def github_traffic(self, ctx: commands.Context):
        fields = []
        traffic_data = self.antistasi_repo.get_views_traffic()
        fields.append(self.bot.field_item(name="Overall", value=f"Amount: {traffic_data.get('count')}\nUnique: {traffic_data.get('uniques')}"))
        for date_views in traffic_data.get('views'):
            fields.append(self.bot.field_item(name=date_views.timestamp.date(), value=f"Amount: {date_views.count}\nUnique: {date_views.uniques}"))

        embed_data = await self.bot.make_generic_embed(title="Traffic for the Antistasi Repo", fields=fields, url=self.antistasi_repo_url)
        await ctx.send(**embed_data)

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    @ asynccontextmanager
    async def _make_other_source_code_images(self, scode: str):
        lexer = await self.bot.execute_in_thread(guess_lexer, scode)
        image = await self.bot.execute_in_thread(highlight, scode, lexer, ImageFormatter(style=self.code_style,
                                                                                         font_name='Fira Code',
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

    async def download_to_string(self, file):
        async with self.bot.aio_request_session.get(file.download_url) as _response:
            if RequestStatus(_response.status) is RequestStatus.Ok:
                return await _response.text('utf-8', 'ignore')

    async def all_repo_files(self, branch_name: str = 'unstable', folder: str = ""):
        for item in await self.bot.execute_in_thread(self.antistasi_repo.get_contents, folder, branch_name):
            if 'jeroenarsenal' not in item.path.casefold() and 'upsmon' not in item.path.casefold():
                if item.type == 'dir':
                    async for file in self.all_repo_files(branch_name=branch_name, folder=item.path):
                        yield file
                else:
                    yield item


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
    bot.add_cog(attribute_checker(GithubCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
