
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
import asyncio
from textwrap import dedent
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Union, Set, Tuple, Dict, IO, Callable, Iterable, Any
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
from fuzzywuzzy import process as fuzzprocess
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty, delete_message_if_text_channel, loop_starter, loop_stopper
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, log_invoker, owner_or_admin
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
    is_online_messages_data_file = pathmaker(APPDATA["json_data"], "is_online_messages.json")
    stored_reasons_data_file = pathmaker(APPDATA["json_data"], "stored_reasons.json")

    required_files = [RequiredFile(already_notified_savefile, [], RequiredFile.FileType.JSON),
                      RequiredFile(is_online_messages_data_file, {}, RequiredFile.FileType.JSON),
                      RequiredFile(stored_reasons_data_file, {}, RequiredFile.FileType.JSON)]
    server_logos = {'mainserver_1': "https://i.postimg.cc/d0Y0krSc/mainserver-1-logo.png",
                    "mainserver_2": "https://i.postimg.cc/BbL8csTr/mainserver-2-logo.png"}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.server_items = self.load_server_items()
        self.stored_server_messages = []
        self.color = 'yellow'
        self.ready = False

        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


# endregion [Init]

# region [Properties]


    @property
    def server_message_remove_time(self) -> int:
        return COGS_CONFIG.retrieve(self.config_name, 'server_message_delete_after_seconds', typus=int, direct_fallback=300)

    @property
    def already_notified_log_items(self) -> set:
        return set(loadjson(self.already_notified_savefile))

    @property
    def server_names(self) -> list:
        return COGS_CONFIG.retrieve(self.config_name, "server_names", typus=List[str], direct_fallback=[])

    @property
    def notification_channel(self) -> discord.TextChannel:
        name = COGS_CONFIG.retrieve(self.config_name, 'status_change_notification_channel', typus=str, direct_fallback='bot-testing')
        return self.bot.channel_from_name(name)

    @property
    def oversize_notification_user(self) -> discord.Member:
        return self.bot.get_antistasi_member(576522029470056450)

    @property
    def is_online_messages(self) -> dict:
        return loadjson(self.is_online_messages_data_file)

    @property
    def is_online_messages_channel(self) -> discord.TextChannel:
        name = COGS_CONFIG.retrieve(self.config_name, 'is_online_messages_channel', typus=str, direct_fallback="bot-testing")
        return self.bot.channel_from_name(name)

    @property
    def stored_reasons(self) -> dict:
        return loadjson(self.stored_reasons_data_file)
# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        await ServerItem.ensure_client()
        for loop_object in self.loops.values():
            loop_starter(loop_object)

        for server in self.server_items:
            await server.is_online()
        await asyncio.gather(*[server.gather_log_items() for server in self.server_items])

        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await ServerItem.ensure_client()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=5, reconnect=True)
    async def check_server_online_loop(self):
        if self.ready is False or self.bot.setup_finished is False:
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
                        data = list(self.already_notified_log_items) + [log_item.path]

                        await asyncio.to_thread(writejson, data, self.already_notified_savefile)
                await asyncio.sleep(0)

    @tasks.loop(minutes=2, reconnect=True)
    async def is_online_message_loop(self):
        if self.ready is False or self.bot.setup_finished is False:
            return
        for server in self.server_items:
            if server.is_online_message_enabled is True:
                asyncio.create_task(self._update_is_online_messages(server), name=f"update_is_online_message_{server.name}")
            else:
                asyncio.create_task(self._delete_is_online_message(server), name=f"remove_is_online_message_{server.name}")
        log.info("Updated 'is_online_messages'")
# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(aliases=['server', 'servers', 'server?', 'servers?'], categories=[CommandCategory.GENERAL])
    @allowed_channel_and_allowed_role()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def current_online_server(self, ctx: commands.Context):
        """
        Shows all server of the Antistasi Community, that are currently online.

        Example:
            @AntiPetros current_online_server
        """
        for server in self.server_items:
            if await server.is_online() is ServerStatus.ON and server.show_in_server_command is True:
                async with ctx.typing():
                    embed_data = await server.make_server_info_embed()
                msg = await ctx.send(**embed_data, delete_after=self.server_message_remove_time, allowed_mentions=discord.AllowedMentions.none())
                await msg.add_reaction(self.bot.armahosts_emoji)
        await delete_message_if_text_channel(ctx, delay=self.server_message_remove_time)

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

    @auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS])
    @allowed_channel_and_allowed_role()
    async def community_server_log_file(self, ctx: commands.Context, amount: Optional[int] = 1, server_name: Optional[str] = 'mainserver_1'):
        if amount > 5:
            await ctx.send('You requested more files than the max allowed amount of 5, aborting!')
            return
        server = await self._get_server_by_name(server_name)
        for i in range(amount):
            item = server.log_items[i]
            if item.is_over_threshold is False:
                async with ctx.typing():
                    embed_data = await item.content_embed()
                await ctx.send(**embed_data)
        await delete_message_if_text_channel(ctx, delay=15)

    # @auto_meta_info_command()
    # async def trigger_server_switch(self, ctx: commands.Context):
    #     server = await self._get_server_by_name('mainserver_1')
    #     await self.send_server_notification(server, ServerStatus.ON)

    @auto_meta_info_command(alias=['restart_reason'], categories=[CommandCategory.ADMINTOOLS])
    @owner_or_admin()
    @log_invoker(log, "info")
    async def set_server_restart_reason(self, ctx: commands.Context, notification_msg_id: int, *, reason: str):
        if notification_msg_id not in set(self.stored_server_messages):
            await ctx.send('This message is either to old or not an server change message!')
            return
        if reason.casefold() in self.stored_reasons:
            reason = self.stored_reasons.get(reason.casefold())
        msg = await self.notification_channel.fetch_message(notification_msg_id)
        embed = msg.embeds[0]
        embed.clear_fields()
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Reason set by', value=ctx.author.mention, inline=False)
        await msg.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    async def clear_all_is_online_messages(self, ctx: commands.Context):
        for server in self.server_items:
            await self._delete_is_online_message(server)
        await delete_message_if_text_channel(ctx)

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

    async def _get_server_by_name(self, server_name: str):
        server = {server_item.name.casefold(): server_item for server_item in self.server_items}.get(server_name.casefold(), None)
        if server is None:
            server_name = fuzzprocess.extractOne(server_name.casefold(), [server_item.name.casefold() for server_item in self.server_items])[0]
            server = await self._get_server_by_name(server_name)
        return server

    async def send_server_notification(self, server_item: ServerItem, changed_to: ServerStatus):
        title = server_item.pretty_name
        description = f"{server_item.pretty_name} was switched ON" if changed_to is ServerStatus.ON else f"{server_item.pretty_name} was switched OFF"
        thumbnail = self.server_logos.get(server_item.name.casefold(), self.server_symbol)
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=description,
                                                       timestamp=datetime.now(timezone.utc),
                                                       thumbnail=thumbnail,
                                                       footer="armahosts")

        channel = self.notification_channel
        msg = await channel.send(**embed_data)
        await msg.add_reaction(self.bot.armahosts_emoji)
        self.stored_server_messages.append(msg.id)

    async def _make_is_online_embed(self, server: ServerItem):
        description = 'is ONLINE' if server.previous_status is ServerStatus.ON else 'is OFFLINE'
        color = 'green' if server.previous_status is ServerStatus.ON else 'red'
        thumbnail = self.server_logos.get(server.name.casefold(), self.server_symbol)
        embed_data = await self.bot.make_generic_embed(title=server.pretty_name,
                                                       description=description,
                                                       footer='armahosts',
                                                       thumbnail=thumbnail,
                                                       url=self.bot.armahosts_url,
                                                       color=color,
                                                       timestamp=datetime.now(timezone.utc))
        return embed_data

    async def _delete_is_online_message(self, server: ServerItem):
        message_id = self.is_online_messages.get(server.name.casefold())
        if message_id is not None:
            msg = await self.is_online_messages_channel.fetch_message(message_id)
            await msg.delete()
            data = self.is_online_messages.copy()
            del data[server.name.casefold()]
            writejson(data, self.is_online_messages_data_file)

    async def _create_is_online_message(self, server: ServerItem):
        embed_data = await self._make_is_online_embed(server)
        msg = await self.is_online_messages_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        is_online_data = self.is_online_messages
        is_online_data[server.name.casefold()] = msg.id
        writejson(is_online_data, self.is_online_messages_data_file)

    async def _update_is_online_messages(self, server: ServerItem):
        message_id = self.is_online_messages.get(server.name.casefold())
        if message_id is None:
            await self._create_is_online_message(server)
            return
        msg = await self.is_online_messages_channel.fetch_message(message_id)
        embed_data = await self._make_is_online_embed(server)
        await msg.edit(**embed_data, allowed_mentions=discord.AllowedMentions.none())

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
        for loop_object in self.loops.values():
            loop_stopper(loop_object)

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
