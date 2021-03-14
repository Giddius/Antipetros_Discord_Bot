
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
from tempfile import TemporaryDirectory
import asyncio
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory
from textwrap import dedent
from datetime import datetime, timedelta
from typing import Iterable, Union, List
from pprint import pprint
import random
# * Third Party Imports -->
import a2s
from rich import print as rprint, inspect as rinspect
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
from fuzzywuzzy import process as fuzzprocess
import discord
from io import StringIO
from discord.ext import commands, tasks
from webdav3.client import Client
from async_property import async_property
from dateparser import parse as date_parse
from pytz import timezone
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import CogConfigReadOnly, make_config_name, seconds_to_pretty, alt_seconds_to_pretty
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, allowed_channel_and_allowed_role_2, has_attachments, owner_or_admin, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_antistasi_log_watcher_cog import LogServer
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antistasi_template_checker.engine.antistasi_template_parser import run as template_checker_run
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_community_server_info_cog import CommunityServerInfo, ServerStatusChange
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
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

COG_NAME = "CommunityServerInfoCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class CommunityServerInfoCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    soon
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    base_server_info_file = APPDATA['base_server_info.json']
    server_status_change_exclusions_file = pathmaker(APPDATA['json_data'], 'server_status_change_exclusions.json')
    server_symbol = "https://i.postimg.cc/dJgyvGH7/server-symbol.png"
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,
                             "2021-02-18 11:00:11")}

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
        self.servers = None
        self.notification_channel = None
        self.check_server_status_loop_first_run = True
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def server_status_change_exclusions(self):
        if os.path.isfile(self.server_status_change_exclusions_file) is False:
            writejson([], self.server_status_change_exclusions_file)
        return loadjson(self.server_status_change_exclusions_file)

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        self.notification_channel = await self.bot.channel_from_name('bot-testing')
        await self._initialise_server_holder()
        self.check_server_status_loop.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=2)
    async def check_server_status_loop(self):
        if self.check_server_status_loop_first_run is True:
            log.debug('postponing loop "check_server_status_loop", as it should not run directly at the beginning')
            self.check_server_status_loop_first_run = False
            return

        for server_holder in self.servers:
            prev_is_online = server_holder.is_online
            await server_holder.check_is_online()

            if server_holder.is_online is True:
                log.debug("Server %s IS online", server_holder.name)
            else:
                log.debug("Server %s IS NOT online", server_holder.name)
            if server_holder.name not in self.server_status_change_exclusions:
                if server_holder.is_online is True and prev_is_online is False:
                    await self.server_status_notification(server_holder, 'on')

                elif server_holder.is_online is False and prev_is_online is True:
                    await self.server_status_notification(server_holder, 'off')

# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command(enabled=get_command_enabled("current_online_server"))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def current_online_server(self, ctx: commands.Context):
        """
        Shows all server of the Antistasi Community, that are currently online.

        Testserver_3 and Eventserver are excluded as they usually are password guarded.

        Example:
            @AntiPetros current_online_server
        """
        exclude = COGS_CONFIG.retrieve(self.config_name, 'exclude_from_show_online', typus=List[str], direct_fallback=["Testserver_3", 'Eventserver'])
        exclude = set(map(lambda x: x.casefold(), exclude))
        for server_item in self.servers:
            if server_item.name not in exclude:
                try:
                    if server_item.is_online is True:
                        info = await server_item.get_info()
                        player_count = info.player_count
                        max_players = info.max_players
                        map_name = info.map_name
                        ping = round(float(info.ping), ndigits=3)
                        game = info.game
                        password_needed = "YES 🔐" if info.password_protected is True else 'NO 🔓'
                        server_name = info.server_name
                        embed_data = await self.bot.make_generic_embed(title=server_name,
                                                                       thumbnail=self.server_symbol,
                                                                       fields=[self.bot.field_item(name="Server Address", value=str(server_item.address), inline=True),
                                                                               self.bot.field_item(name="Port", value=str(server_item.port), inline=True),
                                                                               self.bot.field_item(name="Teamspeak", value=f"38.65.5.151  {ZERO_WIDTH}  **OR**  {ZERO_WIDTH}  antistasi.armahosts.com"),
                                                                               self.bot.field_item(name="━━━━━━━━━━━━", value=ZERO_WIDTH, inline=False),
                                                                               self.bot.field_item(name="Game", value=game, inline=True),
                                                                               self.bot.field_item(name="Players", value=f"{player_count}/{max_players}", inline=True),
                                                                               self.bot.field_item(name="Ping", value=str(ping), inline=True),
                                                                               self.bot.field_item(name="Map", value=map_name, inline=True),
                                                                               self.bot.field_item(name="Password", value=f"{password_needed}", inline=True),
                                                                               self.bot.field_item(name='Battlemetrics', value="🔗 " + embed_hyperlink('link to Battlemetrics', server_item.battlemetrics_url), inline=True)],
                                                                       author="armahosts",
                                                                       footer="armahosts",
                                                                       color="blue")

                        # mod_list_command = self.bot.get_command('get_newest_mod_data')
                        await ctx.send(**embed_data)
                        # await ctx.invoke(mod_list_command, server_item.name)
                        await asyncio.sleep(0.5)
                except asyncio.exceptions.TimeoutError:
                    server_item.is_online = False

    @auto_meta_info_command(enabled=get_command_enabled("current_players"))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def current_players(self, ctx: commands.Context, *, server: str):
        """
        Show all players that are currently online on one of the Antistasi Community Server.

        Shows Player Name, Player Score and Time Played on that Server.

        Args:
            server (str): Name of the Server, case insensitive.

        Example:
            @AntiPetros current_players mainserver_1
        """
        mod_server = server.strip().replace(' ', '_')
        server_holder = {server_item.name.casefold(): server_item for server_item in self.servers}.get(mod_server.casefold(), None)
        if server_holder is None:
            await ctx.send(f"Can't find a server nammed {server}")
            return
        if server_holder.is_online is False:
            await ctx.send(f"The server, `{server}` is currently not online")
            return
        try:
            player_data = await server_holder.get_players()
            player_data = sorted(player_data, key=lambda x: x.score, reverse=True)
            fields = []
            for player in player_data:
                if player.name:
                    fields.append(self.bot.field_item(name=f"__***{player.name}***__",
                                                      value=f"{ZERO_WIDTH}\n**Score:** {(ZERO_WIDTH+' ')*16} {player.score}\n**Duration:** {(ZERO_WIDTH+' ')*10} {alt_seconds_to_pretty(player.duration, shorten_name_to=3)}\n{'━'*25}", inline=False))
            info = await server_holder.get_info()
            async for embed_data in self.bot.make_paginatedfields_generic_embed(title=f'Online Players on {info.server_name}',
                                                                                thumbnail=self.server_symbol,
                                                                                description=f"Current map is __**{info.map_name}**__",
                                                                                footer={'text': f"Amount Players is {info.player_count}"},
                                                                                fields=fields):
                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        except asyncio.exceptions.TimeoutError:
            await ctx.send(f"The server, `{server}` is currently not online")
            server_holder.is_online = False

    @auto_meta_info_command(enabled=get_command_enabled('exclude_from_server_status_notification'))
    @allowed_channel_and_allowed_role_2()
    @log_invoker(log, 'critical')
    async def exclude_from_server_status_notification(self, ctx: commands.Context, server_name: str):
        if server_name.casefold() not in [server_holder.name.casefold() for server_holder in self.servers]:
            await ctx.send(f'Cannot find Server with the name {server_name}, aborting!')
            return
        if server_name.casefold() in self.server_status_change_exclusions:
            await ctx.send(f'Server {server_name} is already excluded from status change notifications. aborting!')
            return
        await self._add_to_server_status_change_exclusions(server_name)
        await ctx.send(f'Excluded {server_name} from status change notifications')

    @auto_meta_info_command(enabled=get_command_enabled('undo_exclude_from_server_status_notification'))
    @allowed_channel_and_allowed_role_2()
    @log_invoker(log, 'critical')
    async def undo_exclude_from_server_status_notification(self, ctx: commands.Context, server_name: str):
        if server_name.casefold() not in [server_holder.name.casefold() for server_holder in self.servers]:
            await ctx.send(f'Cannot find Server with the name {server_name}, aborting!')
            return
        if server_name.casefold() not in self.server_status_change_exclusions:
            await ctx.send(f"Server {server_name} is currently not excluded from status change notifications, aborting!")
            return
        await self._remove_from_server_status_change_exclusions(server_name)
        await ctx.send(f"Status change notifications have been reenabled for {server_name}")

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

    async def server_status_notification(self, server_item: CommunityServerInfo, switched_to_status: ServerStatusChange):
        status_message = "Was switched ON" if switched_to_status is ServerStatusChange.TO_ON else "Was switched OFF"
        embed_data = await self.bot.make_generic_embed(title=server_item.name.replace('_', ' ').title(), description=status_message,
                                                       fields=[self.bot.field_item(name='UTC Time', value=datetime.utcnow().strftime(self.bot.std_date_time_format)),
                                                               self.bot.field_item(name='Reason', value="")])
        await self.notification_channel.send(**embed_data)

    async def _initialise_server_holder(self):
        self.servers = []
        for name, info in loadjson(self.base_server_info_file).items():
            new_server_holder = CommunityServerInfo(name, **info)
            await new_server_holder.check_is_online()
            if new_server_holder.is_online is True:
                log.debug("Server %s IS online", new_server_holder.name)
            else:
                log.debug("Server %s IS NOT online", new_server_holder.name)
            self.servers.append(new_server_holder)

    async def _add_to_server_status_change_exclusions(self, server_name: str):
        existing_data = self.server_status_change_exclusions
        existing_data.append(server_name.casefold())
        writejson(existing_data, self.server_status_change_exclusions_file)

    async def _remove_from_server_status_change_exclusions(self, server_name: str):
        existing_data = self.server_status_change_exclusions
        existing_data.remove(server_name.casefold())
        writejson(existing_data, self.server_status_change_exclusions_file)

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
        self.check_server_status_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.qualified_name}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(CommunityServerInfoCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
