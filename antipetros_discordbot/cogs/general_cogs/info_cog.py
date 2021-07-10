# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from enum import Enum

import asyncio
import unicodedata
import imgkit
# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property
# * Gid Imports -->
from sortedcontainers import SortedDict, SortedList
import gidlogger as glog
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
# * Local Imports -->
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.engine.replacements.task_loop_replacement import custom_loop

from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle

from typing import TYPE_CHECKING
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, auto_meta_info_command

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


# endregion[Imports]

# region [TODO]

# TODO: Docstring for all non command methods.


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


class InfoCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.GENERAL}):
    """
    Commands to provide several types of stats to the user.
    """
# region [ClassAttributes]

    public = True
    meta_status = CogMetaStatus.WORKING
    long_description = ""
    extra_info = ""
    short_doc = ""
    brief = ""
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

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.time_sorted_guild_member_list = []
        self.color = "red"


# endregion [Init]

# region [Properties]

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
        await super().on_ready_setup()
        if self.bot.antistasi_guild.chunked is False:
            await self.bot.antistasi_guild.chunk(cache=True)
        await self.make_time_sorted_guild_member_list()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus=typus)
        await self.make_time_sorted_guild_member_list()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name='on_member_join')
    async def update_time_sorted_member_ids_join(self, member):
        if self.completely_ready is False:
            return
        await self.make_time_sorted_guild_member_list()

    @commands.Cog.listener(name='on_member_remove')
    async def update_time_sorted_member_ids_remove(self, member):
        if self.completely_ready is False:
            return
        await self.make_time_sorted_guild_member_list()


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_bot(self, ctx: commands.Context):
        """
        Shows Info about the Bot itself.

        Example:
            @AntiPetros info_bot
        """

        name = self.bot.name
        cleaned_prefixes = self.bot.all_prefixes
        insensitive_commands_emoji = '✅' if self.bot.case_insensitive is True else '❎'
        try:
            most_used_command_name, most_used_command_amount = await self.bot.most_invoked_commands()
        except IndexError:
            most_used_command_name, most_used_command_amount = 'None', 0

        data = {"Usable Prefixes": (ListMarker.make_list(cleaned_prefixes, indent=1), False),
                "Case-INsensitive?": (insensitive_commands_emoji, False),
                "Number of Commands": (self.bot.command_amount, True),
                "Most used Command": (f"`{most_used_command_name}` used {most_used_command_amount} times", True),
                "Release Date": (self.bot.launch_date.strftime("%a the %d. of %b, %Y"), True),
                "Version": (self.bot.version, True),
                "Uptime": (self.bot.uptime_pretty, True),
                "Current Latency": (f"{round(self.bot.latency * 1000)} ms", True),
                "Created By": (self.bot.creator.mention, True),
                "Github Link": (embed_hyperlink('Github Repo 🔗', self.bot.github_url), True),
                "Wiki": (embed_hyperlink('Github Wiki 🔗', self.bot.github_wiki_url), True),
                "Invocations since launch": (await self.bot.get_amount_invoked_overall(), True),
                "Roles": (', '.join(role.mention for role in self.bot.roles), False),
                "Last Invocation": (self.bot.last_invocation.strftime(self.bot.std_date_time_format + ' UTC'), True)}

        fields = []
        for key, value in data.items():
            if value[0] not in ['', None]:
                fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
        embed_data = await self.bot.make_generic_embed(title=name,
                                                       description=self.bot.description,
                                                       image=self.bot.portrait_url,
                                                       url=self.bot.github_url,
                                                       fields=fields,
                                                       thumbnail=None,
                                                       typus="info_bot_embed")

        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_guild(self, ctx: commands.Context):
        """
        Shows some info of the Antistasi Guild.

        Example:
            @AntiPetros info_guild
        """
        async with ctx.typing():
            as_guild = self.bot.antistasi_guild
            # await as_guild.chunk()
            thumbnail = None
            image = str(as_guild.banner_url)
            description = as_guild.description
            if description is None:
                description = "This Guild has no description set"

            data = {
                'Amount of Channels overall': (len([await asyncio.sleep(0, channel) for channel in as_guild.channels if channel.type is not discord.ChannelType.category and not channel.name.casefold().startswith('ticket-')]), True),
                'Amount of Text Channels': (len([await asyncio.sleep(0, channel) for channel in as_guild.text_channels if channel.type is not discord.ChannelType.category and not channel.name.casefold().startswith('ticket-')]), True),
                'Amount of Voice Channels': (len(as_guild.voice_channels), True),
                "Amount Members": (len(as_guild.members), True),
                'Amount Custom Emojis': (len(as_guild.emojis), True),
                "Amount Roles": (len(as_guild.roles), True),
                "Current Premium Tier": (as_guild.premium_tier, True),
                "Current Boosts": (as_guild.premium_subscription_count, True),
                'Current File Size Limit': (bytes2human(as_guild.filesize_limit, annotate=True), True),
                "Preferred Locale": (as_guild.preferred_locale, True),
                'Created at': (as_guild.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), False),
                "Owner": (f"{as_guild.owner.mention} (`{as_guild.owner.name}`)", False),
                "Current Booster": ('\n'.join([await asyncio.sleep(0, f"{member.mention} (`{member.name}`)") for member in sorted(as_guild.premium_subscribers, key=lambda x: len(x.display_name))]), False),
                "Rules Channel": (as_guild.rules_channel.mention, False),
                "Member for longest time": (await self._oldest_youngest_member(True), False),
                "Member for shortest time": (await self._oldest_youngest_member(False), False),
                "Most Used Channel": (await self.most_used_channel(), False)
            }

            fields = [self.bot.field_item(name=key, value=str(value[0]), inline=value[1]) for key, value in data.items() if value[0]]

            embed_data = await self.bot.make_generic_embed(title=as_guild.name,
                                                           url="https://antistasi.de/",
                                                           description=description,
                                                           thumbnail=thumbnail,
                                                           fields=fields,
                                                           image=image,
                                                           typus="info_guild_embed")
        await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def info_me(self, ctx: commands.Context):
        """
        Shows info about the invoking user.

        Including `join position`.

        Example:
            @AntiPetros info_me
        """
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
                    'Join Position': (self.time_sorted_guild_member_list.index(member) + 1, True),
                    'Permissions': (permissions, False)}
            fields = []

            for key, value in data.items():
                if value[0] not in ['', None]:
                    fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name,
                                                           description=f"The one and only {member.mention}",
                                                           thumbnail=str(member.avatar_url),
                                                           fields=fields,
                                                           color=member.color,
                                                           typus="info_me_embed")
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(hidden=True, categories=CommandCategory.ADMINTOOLS)
    @owner_or_admin(False)
    @log_invoker(log, 'info')
    async def info_other(self, ctx: commands.Context, member_id: int):
        """
        Same as `info_me`, but about other Users.

        This command is limited to Admins, to prevent user stalking.

        Args:
            member_id (int): id of the user to get info about.

        Example:
            @AntiPetros info_other 576522029470056450
        """
        async with ctx.typing():
            member = await self.bot.fetch_antistasi_member(member_id)
            all_true_permissions = [str(permission) for permission, value in iter(member.guild_permissions) if value is True]
            permissions = "```css\n" + ', '.join(sorted(all_true_permissions)) + '\n```'
            data = {'Id': (f"`{member.id}`", True),
                    'Activity': (str(member.activity), False),
                    'Status': (member.raw_status, True),
                    "Device": ('🖥️ Desktop' if member.is_on_mobile() is False else '📱 Mobile', True),
                    'Roles': ('\n'.join(role.mention for role in sorted(member.roles, key=lambda x: x.position, reverse=True) if "everyone" not in role.name.casefold()), False),
                    'Account Created': (member.created_at.strftime("%H:%M:%S on the %Y.%b.%d"), True),
                    'Joined Antistasi Guild': (member.joined_at.strftime("%H:%M:%S on %a the %Y.%b.%d"), True),
                    'Join Position': (self.time_sorted_guild_member_list.index(member) + 1, True),
                    'Permissions': (permissions, False)}
            fields = []
            for key, value in data.items():
                if value[0] not in ['', None]:
                    fields.append(self.bot.field_item(name=key, value=str(value[0]), inline=value[1]))
            embed_data = await self.bot.make_generic_embed(title=member.name,
                                                           description=f"The one and only {member.mention}",
                                                           thumbnail=str(member.avatar_url),
                                                           fields=fields,
                                                           color=member.color,
                                                           typus="info_other_embed")

        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())


# endregion [Commands]

# region [HelperMethods]


    async def make_time_sorted_guild_member_list(self):
        log.debug("Updating time_sorted_guild_member_id_list.")
        if self.bot.antistasi_guild.chunked is False:
            await self.bot.antistasi_guild.chunk(cache=True)
        self.time_sorted_guild_member_list = SortedList(self.bot.antistasi_guild.members, key=lambda x: x.joined_at)

        log.debug("Finished updating make_time_sorted_guild_member_list.")

    async def _clean_bot_prefixes(self, ctx: commands.Context):
        raw_prefixes = await self.bot.get_prefix(ctx.message)
        cleaned_prefixes = list(set(map(lambda x: x.strip(), raw_prefixes)))
        cleaned_prefixes = [f"`{prefix}`" if not prefix.startswith('<') else prefix for prefix in cleaned_prefixes if '804194400611729459' not in prefix]
        return sorted(cleaned_prefixes, key=lambda x: x.startswith('<'), reverse=True)

    async def _oldest_youngest_member(self, get_oldest=True):
        if not self.time_sorted_guild_member_list:
            await self.make_time_sorted_guild_member_list()
        if get_oldest is True:
            member = self.time_sorted_guild_member_list[0]
            if member is self.bot.antistasi_guild.owner:
                member = self.time_sorted_guild_member_list[1]
        else:
            member = self.time_sorted_guild_member_list[-1]

        join_time = member.joined_at

        return f'{member.mention} (`{member.name}`), joined at {join_time.strftime("%H:%M:%S on %a the %Y.%b.%d")}'

    async def most_used_channel(self):
        stats = await self.bot.get_usage_stats('all')
        channel, amount = stats[0]
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
    bot.add_cog(InfoCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
