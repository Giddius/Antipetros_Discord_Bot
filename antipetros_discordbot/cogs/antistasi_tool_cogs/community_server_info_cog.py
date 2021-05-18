
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
import asyncio
from textwrap import dedent
from datetime import datetime
from typing import List
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
import discord
from discord.ext import commands, tasks
from webdav3.client import Client
from async_property import async_property
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, log_invoker
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.auxiliary_classes.server_item import ServerItem, ServerStatus
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_community_server_info_cog import CommunityServerInfo, ServerStatusChange
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from io import BytesIO
from pprint import pprint
# endregion[Imports]

# region [TODO]

# TODO: Refractor current online server out of method so it can be used with the loop and the command

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

from struct import unpack_from as _unpack_from, calcsize as _calcsize


class CommunityServerInfoCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.DEVTOOLS}):
    """
    Presents infos about the community servers, mods and players.
    """
# region [ClassAttributes]
    public = True
    server_symbol = "https://i.postimg.cc/dJgyvGH7/server-symbol.png"

    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    already_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")

    required_files = [RequiredFile(already_notified_savefile, [], RequiredFile.FileType.JSON)]
# endregion [ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.server_items = self.load_server_items()

        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


# endregion [Init]

# region [Properties]


    @property
    def server_message_remove_time(self):
        return COGS_CONFIG.retrieve(self.config_name, 'server_message_delete_after_seconds', typus=int, direct_fallback=300)

    @property
    def already_notified_log_items(self) -> set:
        return set(loadjson(self.already_notified_savefile))

    @property
    def server_names(self):
        return COGS_CONFIG.retrieve(self.config_name, "server_names", typus=List[str], direct_fallback=[])

    @property
    def notification_channel(self):
        name = COGS_CONFIG.retrieve(self.config_name, 'status_change_notification_channel', typus=str, direct_fallback='bot-testing')
        return self.bot.channel_from_name(name)

    @property
    def oversize_notification_user(self):
        return self.bot.get_antistasi_member(576522029470056450)
# endregion [Properties]

# region [Setup]
    @universal_log_profiler
    async def on_ready_setup(self):

        await ServerItem.ensure_client()

        self.check_server_online_loop.start()
        for server in self.server_items:
            await server.is_online()
        await asyncio.gather(*[server.gather_log_items() for server in self.server_items])

        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        await ServerItem.ensure_client()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=4)
    async def check_server_online_loop(self):
        if self.ready is False:
            return
        log.info("updating Server Items")
        await asyncio.gather(*[server.is_online() for server in self.server_items])
        await asyncio.gather(*[server.gather_log_items() for server in self.server_items])
        log.info("Server Items updated")
        member = self.oversize_notification_user
        for server in self.server_items:
            for log_item in server.log_items:
                if log_item.path not in self.already_notified_log_items:
                    if log_item.is_over_threshold is True:
                        await member.send(f"{log_item.name} in server {server.name} is oversized at {log_item.size_pretty}")
                    if log_item is not server.newest_log_item:
                        data = list(self.already_notified_log_items)
                        data.append(log_item.path)
                        writejson(data, self.already_notified_savefile)
                await asyncio.sleep(0)


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(aliases=['server', 'servers', 'server?', 'servers?'], categories=CommandCategory.GENERAL)
    @allowed_channel_and_allowed_role()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def current_online_server(self, ctx: commands.Context):
        """
        Shows all server of the Antistasi Community, that are currently online.

        Example:
            @AntiPetros current_online_server
        """
        messages = []
        async with ctx.typing():
            for server in self.server_items:
                if await server.is_online() is ServerStatus.ON and server.show_in_server_command is True:
                    embed_data = await server.make_server_info_embed()
                    msg = await ctx.send(**embed_data, delete_after=self.server_message_remove_time, allowed_mentions=discord.AllowedMentions.none())
                    messages.append(msg)
        for msg in messages:
            await msg.add_reaction(self.bot.armahosts_emoji)
        await asyncio.sleep(self.server_message_remove_time, delete_message_if_text_channel(ctx))

    # @auto_meta_info_command(aliases=['players', 'players?'], categories=CommandCategory.GENERAL)
    # @allowed_channel_and_allowed_role()
    # @commands.cooldown(1, 120, commands.BucketType.member)
    # async def current_players(self, ctx: commands.Context, *, server: str = "mainserver_1"):
    #     """
    #     Show all players that are currently online on one of the Antistasi Community Server.

    #     Shows Player Name, Player Score and Time Played on that Server.

    #     Args:
    #         server (str): Name of the Server, case insensitive.

    #     Example:
    #         @AntiPetros current_players mainserver_1
    #     """
    #     mod_server = server.strip().replace(' ', '_')
    #     server_holder = {server_item.name.casefold(): server_item for server_item in self.servers}.get(mod_server.casefold(), None)
    #     if server_holder is None:
    #         await ctx.send(f"Can't find a server nammed {server}", delete_after=120)
    #         return
    #     if server_holder.is_online is False:
    #         await ctx.send(f"The server, `{server}` is currently not online", delete_after=120)
    #         return
    #     try:
    #         player_data = await server_holder.get_players()
    #         player_data = sorted(player_data, key=lambda x: x.score, reverse=True)
    #         fields = []
    #         for player in player_data:
    #             if player.name:
    #                 fields.append(self.bot.field_item(name=f"__***{player.name}***__",
    #                                                   value=f"{ZERO_WIDTH}\n**Score:** {(ZERO_WIDTH+' ')*16} {player.score}\n**Duration:** {(ZERO_WIDTH+' ')*10} {alt_seconds_to_pretty(player.duration, shorten_name_to=3)}\n{'━'*25}", inline=False))
    #         info = await server_holder.get_info()
    #         async for embed_data in self.bot.make_paginatedfields_generic_embed(title=f'Online Players on {info.server_name}',
    #                                                                             thumbnail=self.server_symbol,
    #                                                                             description=f"Current map is __**{info.map_name}**__",
    #                                                                             footer={'text': f"Amount Players is {info.player_count}"},
    #                                                                             fields=fields):
    #             await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none(), delete_after=120)
    #     except asyncio.exceptions.TimeoutError:
    #         await ctx.send(f"The server, `{server}` is currently not online", delete_after=120)
    #         server_holder.is_online = False
    #     await asyncio.sleep(120)
    #     await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    async def send_newest_log_file(self, ctx: commands.Context, server_name: str = 'mainserver_1'):
        async with ctx.typing():
            server = {server_item.name.casefold(): server_item for server_item in self.server_items}.get(server_name.casefold())
            with BytesIO() as bytefile:
                async for chunk in server.newest_log_item.content_iter():
                    bytefile.write(chunk)
                bytefile.seek(0)
                discord_file = discord.File(bytefile, server.newest_log_item.name)
        await ctx.send(file=discord_file)
# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

    async def send_server_notification(self, server_item: ServerItem, changed_to: ServerStatus):
        text = f"{server_item.name} was switched ON" if changed_to is ServerStatus.ON else f"{server_item.name} was switched OFF"
        channel = self.notification_channel
        await channel.send(text)

    def load_server_items(self):
        ServerItem.cog = self
        ServerItem.status_switch_signal.connect(self.send_server_notification)
        _out = []
        for server_name in self.server_names:
            server_adress = COGS_CONFIG.retrieve(self.config_name, f"{server_name.lower()}_address", typus=str, direct_fallback=None)
            _out.append(ServerItem(server_name, server_adress, server_name))
        return _out


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
        self.check_server_online_loop.stop()
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
    bot.add_cog(CommunityServerInfoCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
