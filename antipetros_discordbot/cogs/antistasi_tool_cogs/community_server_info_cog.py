
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
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command, auto_meta_info_group
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.auxiliary_classes.server_item import ServerItem, ServerStatus
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_community_server_info_cog import CommunityServerInfo, ServerStatusChange
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from io import BytesIO
from pprint import pprint
import re

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


class CommunityServerInfoCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.DEVTOOLS}):
    """
    Presents infos about the community servers, mods and players.
    """
# region [ClassAttributes]
    public = True
    server_symbol = "https://i.postimg.cc/dJgyvGH7/server-symbol.png"
    server_symbol_off = "https://i.postimg.cc/NfY8CqFL/server-symbol-off.png"
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    already_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")
    is_online_messages_data_file = pathmaker(APPDATA["json_data"], "is_online_messages.json")
    stored_reasons_data_file = pathmaker(APPDATA["json_data"], "stored_reasons.json")
    server_address_verification_regex = re.compile(r"^(?P<address>[\w\-\.\d]+)\:(?P<port>\d+)$", re.IGNORECASE)

    required_files = [RequiredFile(already_notified_savefile, [], RequiredFile.FileType.JSON),
                      RequiredFile(is_online_messages_data_file, {}, RequiredFile.FileType.JSON),
                      RequiredFile(stored_reasons_data_file, {}, RequiredFile.FileType.JSON)]
    required_config_data = {'base_config': {},
                            'cogs_config': {"server_message_delete_after_seconds": "300",
                                            "server_names": "Mainserver_1, Mainserver_2, Testserver_1, Testserver_2, Eventserver, SOG_server_1, SOG_server_2",
                                            "status_change_notification_channel": "bot-testing",
                                            "is_online_messages_channel": "bot-testing",
                                            "sub_log_folder": "Server",
                                            "base_log_folder": "Antistasi_Community_Logs"}}

    server_logos = {'mainserver_1': "https://i.postimg.cc/d0Y0krSc/mainserver-1-logo.png",
                    "mainserver_2": "https://i.postimg.cc/BbL8csTr/mainserver-2-logo.png"}

    available_server_options = {"report_status_change": "no",
                                "show_in_server_command": "no",
                                "is_online_message_enabled": "no",
                                "exclude_logs": "yes"}
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.server_items = self.load_server_items()
        self.stored_server_messages = []
        self.color = 'yellow'
        self.latest_sever_notification_msg_id = None
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
        for server in self.server_items:
            if server.log_folder is not None:
                _ = await server.get_mod_files()
        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await ServerItem.ensure_client()
        if UpdateTypus.CONFIG in typus:
            self.server_items = self.load_server_items()
        log.debug('cog "%s" was updated', str(self))

    def _ensure_config_data(self):
        super()._ensure_config_data()
        for server_name in self.server_names:
            options = {f"{server_name.casefold()}_report_status_change": "no",
                       f"{server_name.casefold()}_show_in_server_command": "no",
                       f"{server_name.casefold()}_is_online_message_enabled": "no",
                       f"{server_name.casefold()}_exclude_logs": "yes",
                       f"{server_name.casefold()}_address": ""}
            for option_name, option_value in options.items():
                if COGS_CONFIG.has_option(self.config_name, option_name) is False:
                    COGS_CONFIG.set(self.config_name, option_name, str(option_value))


# endregion [Setup]

# region [Loops]


    @tasks.loop(minutes=5, reconnect=True)
    async def check_server_online_loop(self):
        if self.ready is False or self.bot.setup_finished is False:
            return
        log.info("updating Server Items")
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
        await asyncio.gather(*[server.is_online() for server in self.server_items])
        for server in self.server_items:
            if server.is_online_message_enabled is True:
                await self._update_is_online_messages(server)
            else:
                asyncio.create_task(self._delete_is_online_message(server))
        log.info("Updated 'is_online_messages'")
# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def subscription_reaction(self, payload: discord.RawReactionActionEvent):
        """
        Listens to emojis being clicked on the `is_online` messages to then send the user that clicked it, the modlist per DM.

        Removes all other emojis being assigned to the messages.

        """
        if self.ready is False or self.bot.setup_finished is False:
            return
        reaction_member = payload.member

        if payload.channel_id != self.is_online_messages_channel.id:
            return
        if payload.message_id not in set(self.is_online_messages.values()):
            return
        if reaction_member.bot is True:
            return

        try:
            channel = self.bot.get_channel(payload.channel_id)
            message = channel.get_partial_message(payload.message_id)
        except discord.errors.NotFound:
            return

        if payload.emoji != self.bot.server_emoji:
            asyncio.create_task(message.remove_reaction(payload.emoji, reaction_member))
            asyncio.create_task(self.clear_emojis_from_is_online_message())
            return

        server_item = await self._server_from_is_online_message_id(message.id)
        if server_item.previous_status is ServerStatus.OFF or server_item.log_folder is None:
            asyncio.create_task(message.remove_reaction(payload.emoji, reaction_member))
            return

        asyncio.create_task(self._send_to_dm(reaction_member, server_item))
        asyncio.create_task(message.remove_reaction(payload.emoji, reaction_member))
        asyncio.create_task(self.clear_emojis_from_is_online_message())

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

    @auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS])
    @allowed_channel_and_allowed_role()
    async def get_server_logs(self, ctx: commands.Context, amount: Optional[int] = 1, server_name: Optional[str] = 'mainserver_1'):
        """
        Retrieve Log files from the community server.

        Able to retrieve up to the 5 newest log files at once.

        Args:
            amount (Optional[int], optional): How many log files to retrieve. Defaults to 1.
            server_name (Optional[str], optional): Name of the server, is fuzzy-matched. Defaults to 'mainserver_1'.

        Example:
            @AntiPetros get_server_logs 5 mainserver_2
        """
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

    @auto_meta_info_command(alias=['restart_reason'], categories=[CommandCategory.ADMINTOOLS])
    @owner_or_admin()
    @log_invoker(log, "info")
    async def set_server_restart_reason(self, ctx: commands.Context, notification_msg_id: Optional[int] = None, *, reason: str):
        if notification_msg_id is None:
            notification_msg_id = self.latest_sever_notification_msg_id
        if notification_msg_id not in set(self.stored_server_messages) or notification_msg_id is None:
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
    @owner_or_admin()
    async def clear_all_is_online_messages(self, ctx: commands.Context):
        """
        Clears all the `is_online` messages, so they can be rebuilt on the next loop.

        Example:
            @AntiPetros clear_all_is_online_messages
        """
        for server in self.server_items:
            await self._delete_is_online_message(server)
        await delete_message_if_text_channel(ctx)

    async def _parse_options(self, options_string: str):
        options_string = options_string.casefold().strip()
        option_parts = list(map(lambda x: x.strip(), options_string.split(',')))
        _out = {}
        for option_pair in option_parts:
            key, value = map(lambda x: x.strip(), option_pair.split('>'))
            _out[key.casefold()] = value
        return _out

    @auto_meta_info_group(invoke_without_command=False)
    @owner_or_admin()
    async def server_meta(self, ctx: commands.Context):
        pass

    @server_meta.command(name='add')
    async def add_server(self, ctx: commands.Context, server_name: str, server_address: str, *, options: Optional[str] = None):

        options = {} if options is None else await self._parse_options(options)
        if self.server_address_verification_regex.match(server_address) is None:
            await ctx.send(f"Server address `{server_address}` does not seem to have the valid format like example: `nae-ugs1.armahosts.com:2352`")
            return
        server_names = self.server_names
        server_names.append(server_name)
        COGS_CONFIG.set(self.config_name, "server_names", ', '.join(list(set(server_names))))

        if COGS_CONFIG.has_option(self.config_name, f"{server_name.casefold()}_address") is False:
            COGS_CONFIG.set(self.config_name, f"{server_name.casefold()}_address", server_address)
        for av_option in self.available_server_options:
            option_name = f"{server_name.casefold()}_{av_option}"
            value = options.get(av_option, None)
            if value is None and COGS_CONFIG.has_option(self.config_name, option_name) is False:
                COGS_CONFIG.set(self.config_name, option_name, self.available_server_options.get(av_option))
            else:
                COGS_CONFIG.set(self.config_name, option_name, value)

        # TODO: make better reporting of what was set
        await ctx.send(f"Added Server {server_name} to my servers", allowed_mentions=discord.AllowedMentions.none())

    @server_meta.command(name='setting')
    async def change_setting(self, ctx: commands.Context, server_name: str, setting_name: str, setting_value: bool):
        clean_setting_name = setting_name.casefold().replace('-', '_')
        clean_server_name = server_name.casefold()
        if clean_setting_name not in self.available_server_options:
            await ctx.send(f"Unknown option `{setting_name}`,\nAvailable Options:\n{ListMarker.make_list(list(self.available_server_options))}", allowed_mentions=discord.AllowedMentions.none())
            return
        if clean_server_name not in [s_name.casefold() for s_name in self.server_names]:
            await ctx.send(f"Unknown Server Name `{server_name}`\nAvailable Servers:\n{ListMarker.make_list(self.server_names)}", allowed_mentions=discord.AllowedMentions.none())
            return

        COGS_CONFIG.set(self.config_name, f"{clean_server_name}_{clean_setting_name}", str(setting_value))
        await ctx.send(f"Setting `{clean_setting_name}` was set to `{setting_value}` for server `{server_name}`", allowed_mentions=discord.AllowedMentions.none())

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

    async def _send_to_dm(self, member: discord.Member, server: ServerItem):
        try:
            mod_data = await server.get_mod_files()
            embed_data = await self.bot.make_generic_embed(title=server.official_name,
                                                           description=ZERO_WIDTH,
                                                           thumbnail=mod_data.image,
                                                           author="armahosts",
                                                           footer="armahosts",
                                                           color="blue")
            embed_data['files'].append(mod_data.html)
            msg = await member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
            await msg.add_reaction(self.bot.armahosts_emoji)
        except IndexError:
            log.warning("Requesting log files to dm lead to an IndexError with Server %s", server.name)

    async def _server_from_is_online_message_id(self, message_id: int) -> ServerItem:
        server_name = {str(value): key for key, value in self.is_online_messages.items()}.get(str(message_id))
        return {item.name.casefold(): item for item in self.server_items}.get(server_name.casefold())

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
        self.latest_sever_notification_msg_id = msg.id

    async def _make_is_online_embed(self, server: ServerItem):
        description = ZERO_WIDTH
        if server.previous_status is ServerStatus.OFF:
            description = 'is ***OFFLINE***'
        elif server.log_folder is not None:
            description = f"Click the {self.bot.server_emoji} emoji to get the current Mod List"

        color = 'green' if server.previous_status is ServerStatus.ON else 'red'
        thumbnail = self.server_logos.get(server.name.casefold(), self.server_symbol) if server.previous_status is ServerStatus.ON else self.server_symbol_off
        fields = []
        if server.previous_status is ServerStatus.ON:
            info_data = await server.get_info()
            fields.append(self.bot.field_item(name='ON', value="☑️", inline=True))
            fields.append(self.bot.field_item(name="Server Address", value=server.server_address.url, inline=True))
            fields.append(self.bot.field_item(name="Port", value=server.server_address.port, inline=True))
            fields.append(self.bot.field_item(name='Players', value=f"{info_data.player_count}/{info_data.max_players}", inline=True))
            fields.append(self.bot.field_item(name="Map", value=info_data.map_name, inline=True))
        embed_data = await self.bot.make_generic_embed(title=server.official_name if server.official_name is not None else server.pretty_name,
                                                       description=description,
                                                       footer='armahosts',
                                                       thumbnail=thumbnail,
                                                       url=server.battle_metrics_url,
                                                       color=color,
                                                       timestamp=datetime.now(timezone.utc),
                                                       fields=fields)

        return embed_data

    async def _delete_is_online_message(self, server: ServerItem):
        message_id = self.is_online_messages.get(server.name.casefold())
        if message_id is not None:
            try:
                msg = await self.is_online_messages_channel.fetch_message(message_id)
                await msg.delete()
            except discord.NotFound:
                log.info("is online message not found for server %s", server.name)
            data = self.is_online_messages.copy()
            del data[server.name.casefold()]
            writejson(data, self.is_online_messages_data_file)

    async def _create_is_online_message(self, server: ServerItem):
        embed_data = await self._make_is_online_embed(server)
        msg = await self.is_online_messages_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        if server.log_folder is not None or server.previous_status is ServerStatus.ON:
            await msg.add_reaction(self.bot.server_emoji)
        if server.log_folder is None or server.previous_status is ServerStatus.OFF:
            await self._clear_emoji_from_msg(msg.id, True)
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
        asyncio.create_task(msg.edit(**embed_data, allowed_mentions=discord.AllowedMentions.none()))
        asyncio.create_task(self.clear_emojis_from_is_online_message())

    async def clear_emojis_from_is_online_message(self):
        for key, msg_id in self.is_online_messages.items():
            try:
                await self._clear_emoji_from_msg(msg_id)
            except discord.errors.NotFound as e:
                log.error(e, exc_info=True)

    async def _clear_emoji_from_msg(self, msg_id: int, all_reactions: bool = False):
        try:
            msg = await self.is_online_messages_channel.fetch_message(msg_id)
            if all_reactions is True:
                await msg.clear_reactions()
            else:
                for reaction in msg.reactions:
                    async for user in reaction.users():
                        if user.id != self.bot.id:
                            await reaction.remove(user)

        except discord.errors.NotFound as e:
            log.error(e, exc_info=True)

    def load_server_items(self):
        ServerItem.cog = self
        ServerItem.status_switch_signal.connect(self.send_server_notification)
        _out = []
        for server_name in self.server_names:
            server_adress = COGS_CONFIG.retrieve(self.config_name, f"{server_name.lower()}_address", typus=str, direct_fallback=None)
            if not server_adress:
                log.critical("Missing server address for server %s", server_name)
                continue
            log_folder = server_name
            if COGS_CONFIG.retrieve(self.config_name, f"{server_name.lower()}_exclude_logs", typus=bool, direct_fallback=False) is True:
                log_folder = None
            _out.append(ServerItem(server_name, server_adress, log_folder))
        return sorted(_out, key=lambda x: x.priority)


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
