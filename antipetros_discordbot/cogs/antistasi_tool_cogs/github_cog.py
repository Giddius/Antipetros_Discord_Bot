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
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.utility.parsing import parse_command_text_file
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle
from github import Github
from antipetros_discordbot.auxiliary_classes.for_cogs.required_filesystem_item import RequiredFile, RequiredFolder
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

from sqf.parser import parse as sqf_parse
from sqf.interpreter import interpret as sqf_interpret
from sqf.types import Variable
from sqf.parser_types import Comment
from sqf.analyzer import analyze as sqf_analyze

# endregion[Imports]

# region [TODO]

# TODO: Transfer the classattribute urls into the config

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


class GithubCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.DEVTOOLS}):
    """
    WiP
    """
# region [ClassAttributes]

    antistasi_repo_url = "https://github.com/official-antistasi-community/A3-Antistasi"
    antistasi_base_file_url = "https://github.com/official-antistasi-community/A3-Antistasi/blob/"
    antistasi_repo_identifier = "official-antistasi-community/A3-Antistasi"

    code_style_map = {'dracula': DraculaStyle,
                      'tomorrow': TomorrowStyle,
                      'tomorrownight': TomorrownightStyle,
                      'tomorrownightbright': TomorrownightbrightStyle,
                      'tomorrownightblue': TomorrownightblueStyle,
                      'tomorrownighteighties': TomorrownighteightiesStyle} | {name.casefold(): get_style_by_name(name) for name in get_all_styles()}

    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.CRASHING | CogMetaStatus.DOCUMENTATION_MISSING
    required_config_data = {'cogs_config': {'code_style': 'dracula'},
                            'base_config': {}}
# endregion [ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.github_access = Github(os.getenv('GITHUB_TOKEN'))
        self.antistasi_repo = self.github_access.get_repo(self.antistasi_repo_identifier)
        self._all_repo_files = {}
        self.last_updated_files = None
        self.ready = False
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def branches(self):
        return [branch.name for branch in self.antistasi_repo.get_branches()]

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
        self.check_github_update_loop.start()
        await self._load_all_repo_files()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=10, reconnect=True)
    async def check_github_update_loop(self):
        if self.ready is False:
            return
        if self.last_updated_files is None:
            return
        if self.antistasi_repo.updated_at > self.last_updated_files:
            log.debug(ic.format(self.antistasi_repo.updated_at))
            log.debug(ic.format(self.last_updated_files))
            await self._load_all_repo_files()


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    async def get_file(self, ctx: commands.Context, file_name: str):
        async with ctx.typing():

            found_file = self._all_repo_files.get(file_name.casefold(), None)
            if found_file is None:
                await ctx.send(f"no file named `{file_name}` in branch `unstable`")
                return
            content = await self.download_to_string(found_file)
            function_calls = await self._find_function_calls(content)

            a3a_function_calls_value = '\n'.join(f"`{item}`" for item in function_calls.get('a3a'))
            if len(a3a_function_calls_value) >= 950:
                a3a_function_calls_value = a3a_function_calls_value[:950].rstrip('`') + '...`'
            if not a3a_function_calls_value:
                a3a_function_calls_value = 'None'

            bis_function_calls_value = '\n'.join(f"`{item}`" for item in function_calls.get('bis'))
            if len(bis_function_calls_value) >= 95:
                bis_function_calls_value = bis_function_calls_value[:950].rstrip('`') + '...`'
            if not bis_function_calls_value:
                bis_function_calls_value = 'None'

            comments = list(await self._find_comments(content))
            comments_value = comments[0] if 'params:' in comments[0].casefold() else ''
            if len(comments_value) >= 950:
                comments_value = comments_value[:950] + '...'
            if not comments_value:
                comments_value = 'None'
            else:
                comments_value = '\n'.join(line.strip('/*') for line in comments_value.splitlines())
                comments_value = "```fix\n" + dedent(comments_value) + '\n```'

            async with self._make_other_source_code_images(content) as source_image_binary:

                embed_data = await self.bot.make_generic_embed(title=file_name,
                                                               url=found_file.html_url,
                                                               description=embed_hyperlink("link to file", found_file.html_url),
                                                               thumbnail=discord.File(source_image_binary, filename=file_name.split(".")[0] + '.png'),
                                                               fields=[self.bot.field_item(name='A3A Function Calls', value=a3a_function_calls_value),
                                                                       self.bot.field_item(name='BIS Function Calls', value=bis_function_calls_value),
                                                                       self.bot.field_item(name='Comments', value=comments_value)])
                with StringIO() as content_file:
                    content_file.write(content)
                    content_file.seek(0)
                    file = discord.File(content_file, file_name)
                    await ctx.send(file=file)
                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    async def github_referals(self, ctx: commands.Context):
        fields = []
        for referal in self.antistasi_repo.get_top_referrers():
            fields.append(self.bot.field_item(name=referal.referrer, value=f"Amount: {referal.count}\nUnique: {referal.uniques}", inline=False))
        embed_data = await self.bot.make_generic_embed(title="Referals to the Antistasi Repo", fields=fields, url=self.antistasi_repo_url)
        await ctx.send(**embed_data)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
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

    @universal_log_profiler
    async def _find_comments(self, file_content: str):
        parsed_content = sqf_parse(file_content)
        all_comments = (str(var) for var in parsed_content.get_all_tokens() if isinstance(var, Comment))
        return all_comments

    @universal_log_profiler
    async def _find_function_calls(self, file_content: str):
        parsed_content = sqf_parse(file_content)
        all_variables = list(set(str(var) for var in parsed_content.get_all_tokens() if isinstance(var, Variable)))
        _out = {'bis': [],
                'a3a': []}
        for variable in all_variables:
            if variable.startswith('BIS_'):
                _out['bis'].append(variable)
            elif variable.startswith('A3A_'):
                _out['a3a'].append(variable)
        return _out

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

    @universal_log_profiler
    async def download_to_string(self, file):
        async with self.bot.aio_request_session.get(file.download_url) as _response:
            if RequestStatus(_response.status) is RequestStatus.Ok:
                return await _response.text('utf-8', 'ignore')

    @universal_log_profiler
    async def all_repo_files(self, branch_name: str = 'unstable', folder: str = ""):
        for item in await asyncio.to_thread(self.antistasi_repo.get_contents, folder, branch_name):
            if 'jeroenarsenal' not in item.path.casefold() and 'upsmon' not in item.path.casefold():
                if item.type == 'dir':
                    async for file in self.all_repo_files(branch_name=branch_name, folder=item.path):
                        yield file
                else:
                    yield await asyncio.sleep(0, item)

    async def _load_all_files_from_branch(self):

        try:
            async for file in self.all_repo_files():
                self._all_repo_files[file.name.casefold()] = file
        except Exception as error:
            log.error(error, exc_info=True)
        log.debug("finished loading github branch  files")

    @universal_log_profiler
    async def _load_all_repo_files(self):
        self._all_repo_files = {}

        asyncio.create_task(self._load_all_files_from_branch())
        self.last_updated_files = datetime.now()

# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx):
        return True

    # async def cog_command_error(self, ctx, error):
    #     pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def cog_unload(self):
        self.check_github_update_loop.stop()
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
    bot.add_cog(GithubCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
