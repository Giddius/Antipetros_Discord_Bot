# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from typing import List, Optional, TYPE_CHECKING, Union
from datetime import datetime, timedelta, timezone
import asyncio
from functools import cached_property
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pprint import pprint
# * Third Party Imports -->
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
from statistics import mean
import aiohttp
import discord
from antipetros_discordbot.utility.converters import GitHubLabelConverter, GithubLabelOperatorConverter
from rapidfuzz import fuzz
from rapidfuzz import process as fuzzprocess
import random
from discord.ext import tasks, commands, flags
from async_property import async_property
import re
# * Gid Imports -->
import gidlogger as glog
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib import cm
import matplotlib.dates as mdates
# * Local Imports -->
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus, GithubLabelOperator
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker
from antipetros_discordbot.utility.pygment_styles import DraculaStyle
from antipetros_discordbot.engine.replacements.task_loop_replacement import custom_loop
from github import Github
import github
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from collections import defaultdict
from sqf.parser import parse as sqf_parse
from sqf.interpreter import interpret as sqf_interpret
from sqf.types import Variable
from sqf.parser_types import Comment
from sqf.analyzer import analyze as sqf_analyze
from antipetros_discordbot.abstracts.connect_signal import AbstractConnectSignal
from antipetros_discordbot.utility.exceptions import ParameterErrorWithPossibleParameter
from antipetros_discordbot.utility.emoji_handling import ALPHABET_EMOJIS, CROSS_MARK_BUTTON_EMOJI, NUMERIC_EMOJIS
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty, delete_specific_message_if_text_channel, loop_starter
from functools import reduce
from antipetros_discordbot.utility.gidtools_functions import bytes2human
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, get_named_colors_mapping
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


class GithubRateLimitHitSignal(AbstractConnectSignal):
    async def emit(self, reset_time: datetime):
        await super().emit(reset_time)


class BranchItem:
    bot = None
    github_client = None
    antistasi_repo = None
    rate_limit_hit = GithubRateLimitHitSignal()
    is_waiting_for_rate_limit_reset = False
    reset_time = None
    answer_time = 180
    code_extensions = {'sqf', 'cpp', 'hpp', 'txt', 'json', 'ps1', 'yml', 'fsm', 'ext', 'sqm'}
    code_highlighter_style = DraculaStyle
    _main_branch_name = None

    def __init__(self, branch_name: str, branch: github.Branch) -> None:
        self.name = branch_name
        self.files = None
        self.branch = branch
        self.url = self.antistasi_repo.html_url + '/tree/' + self.name

    @classmethod
    async def async_init(cls, branch_name: str):
        branch = await asyncio.to_thread(cls.antistasi_repo.get_branch, branch_name)
        branch_item = cls(branch_name, branch)
        if branch_name == cls.main_branch_name:
            log.debug("branch_name=%s, main_branch_name=%s, !branch is main branch! -> loading files", branch_name, cls.main_branch_name)
            asyncio.create_task(branch_item.gather_files())

        return branch_item

    @classmethod
    @property
    def main_branch_name(cls):
        if cls._main_branch_name is None:
            cls._main_branch_name = cls.antistasi_repo.default_branch
        return cls._main_branch_name

    @classmethod
    @property
    def rate_limit_left(cls):
        return cls.github_client.rate_limiting[0]

    @property
    def latest_commit(self):
        return self.branch.commit

    @property
    def latest_commit_date(self):
        return self.latest_commit.commit.author.date

    @property
    def latest_sha(self):
        return self.latest_commit.sha

    @classmethod
    async def _wait_for_rate_limit_reset(cls):
        now = datetime.now(timezone.utc)
        while now < cls.reset_time:
            now = await asyncio.sleep(10, datetime.now(timezone.utc))
        cls.is_waiting_for_rate_limit_reset = False
        cls.reset_time = None

    @classmethod
    async def check_rate_limit_used_up(cls):
        if cls.is_waiting_for_rate_limit_reset is True:
            return
        if cls.rate_limit_left < 2:
            cls.is_waiting_for_rate_limit_reset = True
            cls.reset_time = datetime.fromtimestamp(cls.github_client.rate_limiting_resettime).astimezone(timezone.utc)
            await cls.rate_limit_hit.emit(cls.reset_time)
            asyncio.create_task(cls._wait_for_rate_limit_reset())

    async def get_tree_files(self):
        tree = await asyncio.to_thread(self.antistasi_repo.get_git_tree, self.latest_sha, True)
        for item in tree.tree:
            if '.' in os.path.basename(item.path):
                yield item

    async def gather_files(self):
        await self.check_rate_limit_used_up()
        if self.is_waiting_for_rate_limit_reset is True:
            await discord.utils.sleep_until(self.reset_time)

        self.files = defaultdict(list)

        async for item in self.get_tree_files():
            path = item.path
            name = os.path.basename(path).casefold()
            self.files[name].append(path)

        for name in list(self.files):

            self.files[name.removeprefix('fn_')] = self.files.get(name)
            self.files[name.split('.')[0]] = self.files.get(name)
            self.files[name.split('.')[0].removeprefix('fn_')] = self.files.get(name)

        log.info("finished collecting all files for branch %s", self)

    async def _resolve_multiple_file_choice(self, file_name: str, file_paths: List[str], msg: discord.Message):

        emoji_list = NUMERIC_EMOJIS if len(file_paths) <= 11 else ALPHABET_EMOJIS
        buttons = {CROSS_MARK_BUTTON_EMOJI: 'cancel'}
        title = 'Please Select'
        description = f"Multiple files found for file `{file_name}`.\nPlease select the one you want me to fetch!"
        timestamp = datetime.now(timezone.utc) + timedelta(seconds=self.answer_time)
        fields = [self.bot.field_item(name='Time to answer', value=alt_seconds_to_pretty(self.answer_time), inline=False),
                  self.bot.field_item(name='Cancel', value=f"Press {CROSS_MARK_BUTTON_EMOJI}")]
        for index, file_path in enumerate(file_paths):
            fields.append(self.bot.field_item(name=file_path, value=f"Press {emoji_list[index]}", inline=False))
            buttons[emoji_list[index]] = index

        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=description,
                                                       fields=fields,
                                                       thumbnail=None,
                                                       timestamp=timestamp,
                                                       author={'name': self.name, 'url': self.url, 'icon_url': self.bot.antistasi_image})

        confirm_message = await msg.channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False))
        for button in buttons:
            await confirm_message.add_reaction(button)

        def check_answer(payload: discord.RawReactionActionEvent):
            emoji_string = str(payload.emoji)

            return all([payload.channel_id == msg.channel.id,
                        payload.member.id == msg.author.id,
                        emoji_string in set(buttons)])

        try:
            payload = await self.bot.wait_for('raw_reaction_add', timeout=self.answer_time, check=check_answer)
            await msg.channel.trigger_typing()
            await delete_specific_message_if_text_channel(confirm_message)
        except asyncio.TimeoutError:
            await delete_specific_message_if_text_channel(confirm_message)
            timeout_embed = await self.bot.make_cancelled_embed(title='Time-out', msg=f'Fetching of file was cancelled as no answer was received for {alt_seconds_to_pretty(self.answer_time)}')
            await msg.channel.send(embed=timeout_embed, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False), delete_after=60)
            return

        answer = buttons.get(str(payload.emoji))
        if answer == 'cancel':
            cancel_embed = await self.bot.make_cancelled_embed(title='Cancelled', msg='Cancelled by User request')
            await msg.channel.send(embed=cancel_embed, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False), delete_after=60)
            return

        return file_paths[answer]

    async def _get_file_data(self, file_path: str) -> github.ContentFile:
        content_item = await asyncio.to_thread(self.antistasi_repo.get_contents, file_path, ref=self.name)
        return content_item

    async def make_code_image(self, path: str, content: Union[str, bytes]):
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors="ignore")

        annotated_content = f"# {path}\n\n" + content
        lexer = await asyncio.to_thread(guess_lexer, annotated_content)
        image = await asyncio.to_thread(highlight, annotated_content, lexer, ImageFormatter(style=self.code_highlighter_style,
                                                                                            font_name='Fira Code',
                                                                                            line_number_bg="#2f3136",
                                                                                            line_number_fg="#ffffff",
                                                                                            line_number_chars=3,
                                                                                            line_pad=5,
                                                                                            font_size=20,
                                                                                            line_number_bold=True))
        return image

    async def get_content_files(self, file_data: github.ContentFile):
        async with self.bot.aio_session.get(file_data.download_url) as _response:
            if RequestStatus(_response.status) is RequestStatus.Ok:
                with BytesIO() as bytefile:
                    byte_data = await _response.read()
                    bytefile.write(byte_data)
                    bytefile.seek(0)
                    content_file = discord.File(bytefile, file_data.name)

        # if file_data.name.split('.')[-1].casefold() in self.code_extensions and file_data.size < (100 * 1024):
        #     thumbnail = await self.make_code_image(file_data.name, byte_data)
        # else:
        #     thumbnail = None
        thumbnail = None
        return thumbnail, content_file

    async def request_file(self, file_name: str, msg: discord.Message):
        if self.files is None:
            await self.gather_files()
        file_paths = self.files.get(file_name.casefold(), None)
        if file_paths is None:
            alternative = fuzzprocess.extractOne(file_name, set(self.files))[0]
            await msg.channel.send(f'File `{file_name}` was not found in branch `{self.name}`\n did you mean `{alternative}`?', allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False), delete_after=60)
            return
        if len(file_paths) > 24:
            pprint(file_paths)
            failed_embed = await self.bot.make_cancelled_embed(title='To many possible files', msg=f"There are too many possible files for file_name `{file_name}`. Max possible is 24!")
            await msg.channel.send(embed=failed_embed, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False))
            return
        if len(file_paths) > 1:
            file_path = await self._resolve_multiple_file_choice(file_name=file_name, file_paths=file_paths, msg=msg)
        else:
            file_path = file_paths[0]
        await msg.channel.trigger_typing()
        if file_path is not None:
            file_data = await self._get_file_data(file_path)
            commit = await asyncio.to_thread(self.antistasi_repo.get_commits, path=file_data.path)
            commit = commit[0]
            thumbnail, content_file = await self.get_content_files(file_data)
            embed_data = await self.bot.make_generic_embed(title=file_data.name,
                                                           fields=[self.bot.field_item(name='Branch', value=embed_hyperlink(self.name, self.url), inline=False),
                                                                   self.bot.field_item(name='Size', value=bytes2human(file_data.size, True), inline=False),
                                                                   self.bot.field_item(name='Last Commit', value=embed_hyperlink(commit.commit.message.split('\n')[0], commit.html_url), inline=False)],
                                                           url=file_data.html_url,
                                                           author={"name": commit.author.login, "url": commit.author.html_url, 'icon_url': commit.author.avatar_url},
                                                           timestamp=commit.commit.author.date,
                                                           thumbnail=thumbnail,
                                                           typus="github_file_embed")
            embed_data['files'].append(content_file)
            await msg.channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, branch={self.branch})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(branch_name={self.name}, branch={self.branch})"


class GithubCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.DEVTOOLS}):
    """
    Dynamic meta info and files from the Antistasi Github.
    """
# region [ClassAttributes]

    antistasi_repo_url = "https://github.com/official-antistasi-community/A3-Antistasi"
    antistasi_base_file_url = "https://github.com/official-antistasi-community/A3-Antistasi/blob/"
    antistasi_repo_identifier = "official-antistasi-community/A3-Antistasi"

    meta_status = CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    required_config_data = {'cogs_config': {"trigger_prefix": '##',
                                            'listen_for_github_request_in_message_enabled': 'no'},
                            'base_config': {}}
    github_webhook_channel_id = 596660987919204353


# endregion [ClassAttributes]

# region [Init]


    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.github_client = Github(os.getenv('GITHUB_TOKEN'))
        self.antistasi_repo = self.github_client.get_repo(self.antistasi_repo_identifier)

        BranchItem.bot = self.bot
        BranchItem.github_client = self.github_client
        BranchItem.antistasi_repo = self.antistasi_repo
        BranchItem.rate_limit_hit.connect(self.notify_creator_rate_limit_hit)
        self.color = 'black'
        self.branches = []
        self.trigger_prefix = COGS_CONFIG.retrieve(self.config_name, 'trigger_prefix', typus=str, direct_fallback='##')
        self.github_request_regex = re.compile(rf"(?:\s|\A)(?P<prefix>{self.trigger_prefix})(?P<branch_name>[\w\-\_\d]+(?:\/))?(?P<request_identifier>\w*\.?\w+)", re.IGNORECASE)
        self.listen_for_github_request_in_message_enabled = None
        self.labels = {}


# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        await super().on_ready_setup()
        await self._update_listener_settings()
        await self.make_branches()
        asyncio.create_task(asyncio.to_thread(self.get_labels))
        self.ready = True

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus=typus)
        asyncio.create_task(asyncio.to_thread(self.get_labels))
        if UpdateTypus.CONFIG in typus:
            await self._update_listener_settings()
            await self._update_trigger_prefix_regex()
        elif UpdateTypus.CYCLIC in typus:
            await self._update_trigger_prefix_regex()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @custom_loop(minutes=5, reconnect=True)
    async def tell_rate_limit_loop(self):
        if self.completely_ready is False:
            return
        log.info("Github Rate limit remaining: %s", self.github_client.rate_limiting[0])

# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name='on_message')
    async def listen_for_github_request_in_message(self, msg: discord.Message):
        if self.completely_ready is False:
            return
        if self.listen_for_github_request_in_message_enabled is False:
            return

        if BranchItem.is_waiting_for_rate_limit_reset is True:
            return

        channel = msg.channel
        author = msg.author
        if self.bot.is_debug is True and channel.id != 645930607683174401:
            return
        if channel.type is discord.ChannelType.private:
            return
        if author.bot is True:
            return

        if channel.id == self.github_webhook_channel_id:
            await self.make_branches()
            return

        request_match = self.github_request_regex.search(msg.content)
        if not request_match:
            return

        prefix, branch_name, request_identifier = request_match.groups()
        if request_identifier.isnumeric():
            request_identifier = int(request_identifier)
            asyncio.create_task(self._send_github_issue(request_identifier, channel, author, msg))

        else:
            asyncio.create_task(self._send_github_file(branch_name, request_identifier, channel, author, msg))


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    async def github_rate_limit_left(self, ctx: commands.Context):
        rate_limit_left = self.github_client.rate_limiting[0]
        await ctx.send(rate_limit_left)

    @auto_meta_info_command(clear_invocation=True, experimental=True)
    @allowed_channel_and_allowed_role()
    async def show_referrers(self, ctx: commands.Context):
        async def _transform_name(name: str) -> str:
            if '.' not in name:
                name = name + '.com'
            if len(name.split('.')[0]) > 1:
                return name[:1].upper() + name[1:]
            else:
                return name
        referrers = self.antistasi_repo.get_top_referrers()
        fig, ax = plt.subplots()
        max_color_val = 256
        max_count = max([item.count for item in referrers])
        max_half = max_count // 2

        def get_rand_color(item):
            part = 1 / (max_count)
            r = max(0.5 - ((part * item.count) / 2), 0)
            g = min(0.1 + ((part * item.count) / 2), 1)
            b = 0.05
            a = 0.5

            return r, g, b, a
        plot_1 = ax.barh([index + 2 for index, item in enumerate(referrers)], [item.count for item in referrers], tick_label=["" for i in range(len(referrers))],
                         align='center', color=[get_rand_color(item) for item in referrers])
        ax.set_title('Top Referrers to the Antistasi Repo (Last 14 days)')
        ax.set_xlabel('Visitors')
        ax.set_ylabel('Referrers', rotation=90)

        for index, data in enumerate(referrers):
            item_name = await _transform_name(data.referrer)
            pos = data.count - 10 if data.count > max_half or (data.count > (max_half // 2) and len(item_name) <= 10) else 10

            text = ax.text(pos, index + 2, item_name, color='white', fontname="Roboto", fontsize=11, fontweight='bold')
            text.set_path_effects([patheffects.Stroke(linewidth=1.25, foreground='black'),
                                   patheffects.Normal()])
            text.set_verticalalignment('center')
            if data.count > max_half or (data.count > (max_half // 2) and len(item_name) <= 10):
                text.set_horizontalalignment("right")
            else:
                text.set_horizontalalignment('left')

        ax.invert_yaxis()

        with BytesIO() as bytefile:
            fig.savefig(bytefile, format='png', dpi=250)

            bytefile.seek(0)
            file = discord.File(bytefile, 'top_github_referrers.png')
        await ctx.send(file=file)
        plt.close('all')

    @auto_meta_info_command(clear_invocation=True, experimental=True)
    @allowed_channel_and_allowed_role()
    async def show_most_popular_file(self, ctx: commands.Context):
        async def get_name(item_path):
            parts = [part for part in item_path.split('/') if part != ""]
            if parts[-1].casefold() == "a3-antistasi":
                if 'tree' in parts:
                    return 'tree/main'
                return 'main'

            new_path = ""

            while parts[0].casefold() != 'a3-antistasi':
                _ = await asyncio.sleep(0, parts.pop(0))

            return '/'.join(parts[1:])
        pop_files = self.antistasi_repo.get_top_paths()
        fig, ax = plt.subplots()
        max_count = max([item.count for item in pop_files])
        max_half = max_count // 2

        def get_rand_color(item):
            part = 1 / (max_count)
            r = max(0.5 - ((part * item.count) / 2), 0)
            g = min(0.1 + ((part * item.count) / 2), 1)
            b = 0.05
            a = 0.5

            return r, g, b, a
        plot_1 = ax.barh([index + 2 for index, item in enumerate(pop_files)], [item.count for item in pop_files], tick_label=["" for i in range(len(pop_files))],
                         align='center', color=[get_rand_color(item) for item in pop_files])
        ax.set_title('Ten most popular content items of the Antistasi Repo')
        ax.set_xlabel('Visitors')
        ax.set_ylabel('Items', rotation=90)
        com_path = os.path.commonpath([item.path for item in pop_files])
        for index, data in enumerate(pop_files):
            item_name = await get_name(data.path)
            pos = 10
            text = ax.text(pos, index + 2, item_name, color='white', fontname="Roboto", fontsize=9, fontweight='bold')
            text.set_path_effects([patheffects.Stroke(linewidth=1.25, foreground='black'),
                                   patheffects.Normal()])
            text.set_verticalalignment('center')
            text.set_horizontalalignment('left')
        ax.invert_yaxis()

        with BytesIO() as bytefile:
            fig.savefig(bytefile, format='png', dpi=250)

            bytefile.seek(0)
            file = discord.File(bytefile, 'popular_files.png')
        await ctx.send(file=file)
        plt.close('all')

    @ auto_meta_info_command()
    @ allowed_channel_and_allowed_role()
    async def list_branches(self, ctx: commands.Context):
        """
        Lists up to 24 of the newest Branches from all branches with changes in the last 90 days.

        Shows date of last change, user and provides a link.

        Example:
            @AntiPetros list_branches
        """
        fields = []
        for branch in sorted(self.branches, key=lambda x: x.latest_commit_date, reverse=True)[:24]:

            fields.append(self.bot.field_item(name=branch.name,
                                              value=ListMarker.make_list(symbol='arrow_down',
                                                                         in_data=[f"`{branch.latest_commit_date.date().strftime('%Y-%m-%d')}`",
                                                                                  f"by {embed_hyperlink(branch.latest_commit.author.login, branch.latest_commit.author.html_url)}", embed_hyperlink("link", branch.url)],
                                                                         indent=1)))

        embed_data = await self.bot.make_generic_embed(title=self.antistasi_repo.name + ' Branches',
                                                       description="The most recently changed branches",
                                                       fields=fields,
                                                       url=self.antistasi_repo_url,
                                                       thumbnail=None)
        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await delete_specific_message_if_text_channel(ctx.message)

    @ auto_meta_info_command()
    async def open_github_issues(self, ctx: commands.Context, since_days_ago: Optional[int] = 31, label_operator: Optional[GithubLabelOperatorConverter] = None, *, labels: GitHubLabelConverter = None):
        """
        Gets all open github issues of the antistasi repo.

        Args:
            since_days_ago (Optional[int], optional): Retrieves only Issues that are younger than this amount of Days. Defaults to 31.
            labels (str, optional): Retrieves only issues with these label and all if None, labels do not need to put in quotes, just separeted by an colon. Defaults to None.

        Example:
            @AntiPetros open_github_issues 7 bug
        """

        if labels is None:
            open_issues = await asyncio.to_thread(self.antistasi_repo.get_issues, state='open', since=datetime.now(timezone.utc) - timedelta(days=since_days_ago))
        else:
            if label_operator is None:
                raise ParameterErrorWithPossibleParameter('label_operator', None, await GithubLabelOperatorConverter.get_possible_params())

            open_issues = await asyncio.to_thread(self.antistasi_repo.get_issues, state='open', since=datetime.now(timezone.utc) - timedelta(days=since_days_ago))

            if label_operator is GithubLabelOperator.AND:
                open_issues = [issue for issue in open_issues if all(label.name in set(item.name for item in issue.labels) for label in labels)]

            elif label_operator is GithubLabelOperator.OR:
                open_issues = [issue for issue in open_issues if any(label.name in set(item.name for item in issue.labels) for label in labels)]

            elif label_operator is GithubLabelOperator.NOT:
                open_issues = [issue for issue in open_issues if any(label.name not in set(item.name for item in issue.labels) for label in labels)]

            elif label_operator is GithubLabelOperator.NOT_ANY:
                open_issues = [issue for issue in open_issues if set(item.name for item in issue.labels).isdisjoint(set(label.name for label in labels))]

        open_issues = sorted(open_issues, key=lambda x: x.created_at, reverse=True)
        title = self.antistasi_repo.name + ' Open Issues'
        url = self.antistasi_repo.html_url + '/issues'

        fields = []

        for issue in open_issues:
            labels = ', '.join(f"{embed_hyperlink(label.name, label.url)}" for label in issue.labels)

            fields.append(
                self.bot.field_item(
                    name=f"***##{issue.number}*** - {issue.title}",
                    value=f"> {embed_hyperlink('link', issue.html_url)}\n> Comments: {issue.comments}\n> Labels: {labels}\n> Author: {embed_hyperlink(issue.user.login,issue.user.html_url)}\n> Created: {issue.created_at.strftime(self.bot.std_date_time_format)}", inline=False
                )
            )

        async for embed_data in self.bot.make_paginatedfields_generic_embed(title=title, url=url, fields=fields, thumbnail="https://avatars0.githubusercontent.com/u/53788409?s=200&v=4"):
            await ctx.send(**embed_data)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role()
    async def all_github_labels(self, ctx: commands.Context):
        await ctx.send(ListMarker.make_list(value.name for value in self.labels.values()))

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    def get_labels(self):
        self.labels = {label.name.casefold(): label for label in self.antistasi_repo.get_labels()}
        return self.labels

    async def _update_listener_settings(self):
        self.listen_for_github_request_in_message_enabled = COGS_CONFIG.retrieve(self.config_name, 'listen_for_github_request_in_message_enabled', typus=bool, direct_fallback=False)

    async def _update_trigger_prefix_regex(self):
        self.trigger_prefix = COGS_CONFIG.retrieve(self.config_name, 'trigger_prefix', typus=str, direct_fallback='##')
        self.github_request_regex = re.compile(rf"(?:\s|\A)(?P<prefix>{self.trigger_prefix})(?P<branch_name>[\w\-\_\d]+(?:\/))?(?P<request_identifier>\w*\.?\w+)", re.IGNORECASE)

    async def get_branch_names(self, min_date: datetime):
        branches = await asyncio.to_thread(self.antistasi_repo.get_branches)
        with ThreadPoolExecutor() as pool:
            for branch in branches:
                latest_commit_data = await self.bot.loop.run_in_executor(pool, lambda x: x.commit.commit.author.date, branch)
                if latest_commit_data > min_date:

                    yield branch.name
                await asyncio.sleep(0)

    async def notify_creator_rate_limit_hit(self, reset_time: datetime):
        message = f"Github rate-limit was hit and will reset at {reset_time.strftime(self.bot.std_date_time_format + ' UTC')}"
        await self.bot.message_creator(message=message)
        log.warning(message)

    async def get_branch_item_by_name(self, query_name: str = None) -> BranchItem:
        if query_name is None:
            query_name = self.antistasi_repo.default_branch
        query_name = query_name.strip('/')
        return {item.name.casefold(): item for item in self.branches}.get(query_name.casefold(), None)

    async def _send_github_file(self, branch_name: str, file_name: str, channel: discord.TextChannel, member: discord.Member, msg: discord.Message):
        branch_item = await self.get_branch_item_by_name(branch_name)
        if branch_item is None:
            await channel.send(f'Branch `{branch_name}` not found', allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False), delete_after=60)
            return

        await branch_item.request_file(file_name, msg)

    async def _send_github_issue(self, issue_number: int, channel: discord.TextChannel, member: discord.Member, msg: discord.Message):
        try:
            issue = await asyncio.to_thread(self.antistasi_repo.get_issue, number=issue_number)
            embed_data = await self.make_issue_embed(issue)
            await channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False))
        except github.GithubException:
            log.warning(f'gihub issue number {issue_number} not found')
            await channel.send(f'Unable to find issue `{issue_number}`', allowed_mentions=discord.AllowedMentions.none(), reference=msg.to_reference(fail_if_not_exists=False))

    async def make_issue_embed(self, issue: github.Issue.Issue):
        title = issue.title
        description = issue.body
        if len(description) > 1024:
            description = description[1020:] + '...'
        url = issue.html_url
        timestamp = issue.created_at
        thumbnail = "https://avatars0.githubusercontent.com/u/53788409?s=200&v=4"
        author = {"name": issue.user.login, "url": issue.user.html_url, "icon_url": issue.user.avatar_url}
        fields = [self.bot.field_item(name='State', value=issue.state, inline=False),
                  self.bot.field_item(name='Amount Comments', value=issue.comments, inline=True),
                  self.bot.field_item(name='Labels', value=ListMarker.make_list([f"`{item.name}`" for item in issue.labels]), inline=False)]
        return await self.bot.make_generic_embed(title=title, description=description, thumbnail=thumbnail, url=url, timestamp=timestamp, fields=fields, author=author, typus='github_issue_embed')

    async def make_branches(self):
        self.branches = []
        min_date = datetime.now() - timedelta(days=90)
        async for branch_name in self.get_branch_names(min_date=min_date):
            asyncio.create_task(self._branch_creation_helper(branch_name))

    async def _branch_creation_helper(self, branch_name):
        self.branches.append(await BranchItem.async_init(branch_name))
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

    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))

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
