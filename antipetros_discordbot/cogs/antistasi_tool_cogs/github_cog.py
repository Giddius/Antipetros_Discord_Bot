# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from typing import TYPE_CHECKING
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
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
import re
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle
from github import Github
import github
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
    Access and meta info about the Antistasi Github. Still WiP
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
    issue_regex = re.compile(r"(?P<issue_id>(?<=\#\#)\d+)")
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.github_access = Github(os.getenv('GITHUB_TOKEN'))
        self.antistasi_repo = self.github_access.get_repo(self.antistasi_repo_identifier)
        self.last_updated_files = None
        self.color = 'black'
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
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
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name='on_message')
    async def send_issue_link(self, msg: discord.Message):
        issue_match = await asyncio.to_thread(self.issue_regex.search, msg.content)
        if issue_match:
            issue_id = issue_match.group('issue_id')
            if issue_id:
                try:
                    issue = self.antistasi_repo.get_issue(number=int(issue_id))
                    channel = msg.channel
                    embed_data = await self.make_issue_embed(issue)
                    await channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), reference=msg)
                except github.GithubException:
                    log.info(f'gihub issue number {issue_id} not found')

# endregion [Listener]

# region [Commands]

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


    async def make_issue_embed(self, issue: github.Issue.Issue):
        title = issue.title
        description = issue.body
        if len(description) > 1024:
            description = description[1020:] + '...'
        url = issue.html_url
        timestamp = issue.created_at
        thumbnail = "https://avatars0.githubusercontent.com/u/53788409?s=200&v=4"
        fields = [self.bot.field_item(name='Created', value=issue.created_at.strftime(self.bot.std_date_time_format), inline=False),
                  self.bot.field_item(name='State', value=issue.state, inline=False)]
        return await self.bot.make_generic_embed(title=title, description=description, thumbnail=thumbnail, url=url, timestamp=timestamp, fields=fields)

    async def _find_comments(self, file_content: str):
        parsed_content = sqf_parse(file_content)
        all_comments = (str(var) for var in parsed_content.get_all_tokens() if isinstance(var, Comment))
        return all_comments

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
        lexer = await asyncio.to_thread(guess_lexer, scode)
        image = await asyncio.to_thread(highlight, scode, lexer, ImageFormatter(style=self.code_style,
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
