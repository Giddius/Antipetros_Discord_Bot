
# region [Imports]


# * Standard Library Imports -->
import os
import json
from typing import TYPE_CHECKING
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Union
from itertools import dropwhile
# * Third Party Imports -->
import a2s
import math
import numpy as np
from textwrap import indent
from rich import print as rprint, inspect as rinspect
# import requests
from pprint import pformat
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
from rapidfuzz import fuzz
from rapidfuzz import process as fuzzprocess
from functools import partial
# * Gid Imports -->
import gidlogger as glog
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, get_named_colors_mapping
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib import cm

import matplotlib.dates as mdates
# * Local Imports -->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel, loop_starter, alt_seconds_to_pretty, rgb256_to_rgb1
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, log_invoker, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus, RequestStatus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command, auto_meta_info_group
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from matplotlib import patheffects
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI
from collections import deque
from antipetros_discordbot.utility.exceptions import TokenMissingError, AskCanceledError, AskTimeoutError
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskFile, AskInput, AskInputManyAnswers, AskAnswer, AskSelectionOptionsMapping, AskSelectionOption, AskSelection
from PIL import Image, ImageEnhance, ImageFilter
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.sqldata_storager import general_db
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
import re
import numpy as np
import scipy as sp
from io import BytesIO
from antipetros_discordbot.utility.sqldata_storager import general_db
from rich.console import Console as RichConsole
from antipetros_discordbot.utility.asyncio_helper import delayed_execution, async_range
from antipetros_discordbot.auxiliary_classes.aux_server_classes import IsOnlineHeaderMessage, ServerItem, ServerStatus
from antipetros_discordbot.utility.debug_helper import console_print
# endregion[Imports]

# region [TODO]

# TODO: Refractor all the current online msg methods and commands

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
console = RichConsole(soft_wrap=True)

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
                                            "base_log_folder": "Antistasi_Community_Logs",
                                            "notify_if_switched_off_also": 'no',
                                            'notification_time_out_seconds': 0,
                                            'request_restart_interaction_enabled': "no",
                                            'request_restart_emoji_name': 'bertha',
                                            'request_mod_data_emoji_name': 'armahosts'}}

    server_logos = {'mainserver_1': "https://i.postimg.cc/d0Y0krSc/mainserver-1-logo.png",
                    "mainserver_2": "https://i.postimg.cc/BbL8csTr/mainserver-2-logo.png"}

    available_server_options = {"report_status_change": "no",
                                "show_in_server_command": "no",
                                "is_online_message_enabled": "no",
                                "exclude_logs": "yes"}
    battlemetrics_api_base_url = "https://api.battlemetrics.com"

    reason_keyword_identifier = '%'
    json_lock = asyncio.Lock()
    db = general_db
    add_amount_lock = asyncio.Lock()
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.server_items = []
        self.color = 'yellow'
        self.latest_sever_notification_msg_id = None
        self.amount_mod_data_requested = 0
        self.amount_restart_requested = 0
        self.halt_is_online_update = False
        self.is_online_message_loop_round = 0
        self.is_online_header_message = None


# endregion [Init]

# region [Properties]

    @property
    def battlemetrics_auth(self):
        if os.getenv('BATTLEMETRICS_TOKEN') is None:
            raise TokenMissingError('BATTLEMETRICS_TOKEN')
        return {'Authorization': f'Bearer {os.getenv("BATTLEMETRICS_TOKEN")}'}

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
    def is_online_messages_channel(self) -> discord.TextChannel:
        name = COGS_CONFIG.retrieve(self.config_name, 'is_online_messages_channel', typus=str, direct_fallback="bot-testing")
        return self.bot.channel_from_name(name)

    @property
    def stored_reasons(self) -> dict:
        return {f'{self.reason_keyword_identifier}{key.casefold()}': value for key, value in loadjson(self.stored_reasons_data_file).items()}

    @property
    def notification_time_out(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notification_time_out_seconds', typus=int, direct_fallback=0)

    @property
    def request_restart_notification_channels(self):
        channel_names = COGS_CONFIG.retrieve(self.config_name, 'request_restart_notification_channel_names', typus=List[str], direct_fallback=["bot-testing"])
        return {self.bot.channel_from_name(channel_name) for channel_name in channel_names}

    @property
    def request_restart_notification_members(self):
        member_ids = COGS_CONFIG.retrieve(self.config_name, "request_restart_notification_member_ids", typus=List[int], direct_fallback=[576522029470056450])
        return {self.bot.get_antistasi_member(member_id) for member_id in member_ids}

    @property
    def request_restart_notification_webhooks(self):
        urls = COGS_CONFIG.retrieve(self.config_name, "request_restart_notification_webhook_urls", typus=List[str], direct_fallback=[
                                    "https://discord.com/api/webhooks/858827398015221800/sD5WMifr7RdP3AbVWVZKgYCPCewTQiMwoWOn0NXUXv8PslisYPWnQcr3IaLy2xaz0ltQ"])
        return {discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(self.bot.aio_session)) for url in urls}

    @ property
    def request_restart_to_notify(self):
        return {'channels': self.request_restart_notification_channels,
                'members': self.request_restart_notification_members,
                'webhooks': self.request_restart_notification_webhooks}

    @property
    def restart_request_timeout(self):
        return COGS_CONFIG.retrieve(self.config_name, "restart_request_timeout_minutes", typus=int, direct_fallback=5)

    @property
    def is_online_interaction_emojis(self):
        emojis = {'request_mod_data': 'armahosts',
                  'request_restart': 'bertha'}
        for key, value in emojis.items():
            name = COGS_CONFIG.retrieve(self.config_name, f'{key}_emoji_name', typus=str, direct_fallback=value)
            emojis[key] = getattr(self.bot, f"{name.casefold()}_emoji")
        return emojis

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await super().on_ready_setup()
        IsOnlineHeaderMessage.cog = self
        self.is_online_header_message = await IsOnlineHeaderMessage.load()

        await self.load_server_items()

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus)

        if UpdateTypus.CONFIG in typus:
            self.is_online_header_message = await IsOnlineHeaderMessage.load()
            await self.load_server_items()
            log.debug("reloaded server Items because of Update signal %s", typus)

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

    @ tasks.loop(minutes=4, reconnect=True)
    async def update_logs_loop(self):
        if self.completely_ready is False:
            return

        member = self.oversize_notification_user
        log.info('Trying to update logs!')
        await asyncio.gather(*[server.update_log_items() for server in self.server_items])
        for server in self.server_items:

            for log_item in server.log_items:
                if log_item.path not in self.already_notified_log_items:
                    if log_item.is_over_threshold is True:
                        await member.send(f"{log_item.name} in server {server.name} is oversized at {log_item.size_pretty}")
                    if log_item is not server.newest_log_item:
                        data = list(self.already_notified_log_items) + [log_item.path]

                        await asyncio.to_thread(writejson, data, self.already_notified_savefile)
                await asyncio.sleep(0)

    @ tasks.loop(seconds=120, reconnect=True)
    async def is_online_message_loop(self):
        if self.completely_ready is False:
            return
        await asyncio.gather(*[server.is_online() for server in self.server_items])
        log.info("updated online status of server_items")
        self.is_online_message_loop_round += 1
        if self.is_online_message_loop_round % 2 == 0 and self.halt_is_online_update is False:
            await self.is_online_header_message.update()
            for server in self.server_items:

                await server.is_online_message.update()
            log.info("Updated 'is_online_messages'")
# endregion [Loops]

# region [Listener]

    @ commands.Cog.listener(name='on_raw_reaction_add')
    async def is_online_mod_list_reaction_listener(self, payload: discord.RawReactionActionEvent):
        """
        Listens to emojis being clicked on the `is_online` messages to then send the user that clicked it, the modlist per DM.

        Removes all other emojis being assigned to the messages.

        """
        if self.completely_ready is False:
            return

        reaction_member = payload.member if payload.member is not None else self.bot.get_antistasi_member(payload.user_id)

        if reaction_member.bot is True:
            return
        if payload.channel_id != self.is_online_messages_channel.id:
            return
        if payload.message_id not in await self.db.get_is_online_message_ids():
            return

        try:
            message = await self.bot.get_message_directly(payload.channel_id, payload.message_id)

        except discord.errors.NotFound:
            return

        server_item = await self._server_from_is_online_message_id(message.id)

        asyncio.create_task(server_item.is_online_message.handle_reaction(reaction=payload.emoji, member=reaction_member))

# endregion [Listener]

# region [Commands]

    @ auto_meta_info_command(aliases=['server', 'servers', 'server?', 'servers?'], categories=[CommandCategory.GENERAL], clear_invocation=True, confirm_command_received=True)
    @ allowed_channel_and_allowed_role()
    @ commands.cooldown(1, 60, commands.BucketType.channel)
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

    @ auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS], aliases=['get_logs'], confirm_command_received=True, clear_invocation=True)
    @ allowed_channel_and_allowed_role()
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
            await asyncio.sleep(2)

    @ auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS], experimental=True)
    @ allowed_channel_and_allowed_role()
    async def only_log_level(self, ctx: commands.Context, level: str = 'error'):
        server = await self._get_server_by_name('mainserver_1')
        text = await server.log_parser.get_only_level(level)
        with BytesIO() as bytefile:
            bytefile.write(text.encode('utf-8', errors='ignore'))
            bytefile.seek(0)
            file = discord.File(bytefile, f'only_level_{level}.log')
        await ctx.send(file=file)

    @ auto_meta_info_command(aliases=['restart_reason'], categories=[CommandCategory.ADMINTOOLS], logged=True, rest_is_raw=True, clear_invocation=True)
    @allowed_channel_and_allowed_role(False)
    async def set_server_restart_reason(self, ctx: commands.Context, notification_msg_id: Optional[int] = None, *, reason: str):
        """
        Sets a reason to the embed of a server restart.

        The reason can either be a text or a key word that points to a stored reason, in which case the stored reason text gets set as reason.

        Args:
            reason (str): either the reason as text, does not need quotes `"` around it, or a keyword of a previous stored reason.
            notification_msg_id (Optional[int], optional): The message id of the server restart message. Defaults to the last server restart message the bot posted.

        Example:
            @AntiPetros restart_reason Petros started dancing uncontrolled.

        Info:
            The command also puts the user who set the reason into the server-restart message. This command can be used multiple times. Best used from Bot-commands channel or Bot-testing channel.

        """
        if not reason:
            await ctx.send(f"It seems the reason is empty (reason: `{reason}`), a reason is needed!", delete_after=120)
            return
        if notification_msg_id is None and ctx.message.reference is None:
            notification_msg_id = self.latest_sever_notification_msg_id

        elif notification_msg_id is None and ctx.message.reference is not None:
            notification_msg_id = ctx.message.reference.message_id

        msg = await self.notification_channel.fetch_message(notification_msg_id)

        if reason.strip().casefold().startswith(self.reason_keyword_identifier):
            reason = self.stored_reasons.get(reason.strip().casefold(), None)
            if reason is None:
                await ctx.send(f"I was unable to find a stored reason for the keyword `{reason}`.\nNo reason was set for {msg.jump_link}", allowed_mentions=discord.AllowedMentions.none(), delete_after=120)
                return
        embed = msg.embeds[0]
        local_time_field = embed.fields[-1]
        utc_time_field = embed.fields[-2]
        embed.clear_fields()
        embed.add_field(name='Reason', value=CodeBlock(reason, 'fix'), inline=False)
        embed.add_field(name='Reason set by', value=f"{ctx.author.mention} at `{datetime.now(tz=timezone.utc).strftime(self.bot.std_date_time_format)} UTC`", inline=False)
        embed.add_field(name=utc_time_field.name, value=utc_time_field.value, inline=False)
        embed.add_field(name=local_time_field.name, value=local_time_field.value, inline=False)

        await msg.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @ auto_meta_info_command(categories=[CommandCategory.ADMINTOOLS], aliases=['add-reason'], logged=True, rest_is_raw=True, clear_invocation=True)
    @ allowed_channel_and_allowed_role()
    async def add_restart_reason(self, ctx: commands.Context, *, reason_line: str):
        if "==" not in reason_line:
            await ctx.send("The reason to add must have the format `name==text`!", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
            return
        name, text = map(lambda x: x.strip(), reason_line.split('==', 1))
        if " " in name:
            await ctx.send("the name for the reason cannot contain spaces!", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
            return
        if name == '':
            await ctx.send(f"name seems to be empty, name: `{name}`", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
            return
        if text == "":
            await ctx.send(f"The text seems to be empty, text: `{text}`", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
            return

        cleaned_name = name.casefold().lstrip(self.reason_keyword_identifier)
        stored_reasons = self.stored_reasons

        if self.reason_keyword_identifier + cleaned_name in stored_reasons:
            already_stored_reason = stored_reasons[f"{self.reason_keyword_identifier}{name}"]
            code_block = CodeBlock(f'Name: {name}\n\n"{already_stored_reason}"', 'fix')
            await ctx.send(f"The name `{name}` is already assigned to an stored reason!\n\n{code_block}", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
            return
        stored_reasons[cleaned_name] = text
        writejson({key.strip(self.reason_keyword_identifier): value for key, value in stored_reasons.items()}, self.stored_reasons_data_file)
        code_block = CodeBlock(f'Name: {name}\n\n"{text}"')
        await ctx.send(f"{code_block}\n\n Was added to the stored reasons and can be use with `{self.reason_keyword_identifier}{name}`", allowed_mentions=discord.AllowedMentions.none(), delete_after=120)

    @ auto_meta_info_command(categories=[CommandCategory.ADMINTOOLS], aliases=['list-reasons'], clear_invocation=True)
    @ allowed_channel_and_allowed_role()
    async def list_stored_restart_reasons(self, ctx: commands.Context):
        fields = [self.bot.field_item(name=name.strip(self.reason_keyword_identifier), value=CodeBlock(value, 'fix'), inline=False) for name, value in self.stored_reasons.items()]
        title = "Stored Restart Reasons"
        description = f"To use the reason, prefix them with `{self.reason_keyword_identifier}` (no space in between).\nExample: `{self.reason_keyword_identifier}disconnect`"
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title=title, description=description, fields=fields, thumbnail=None):
            await ctx.author.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)

    @ auto_meta_info_command()
    @ owner_or_admin()
    async def clear_all_is_online_messages(self, ctx: commands.Context):
        """
        Clears all the `is_online` messages, so they can be rebuilt on the next loop.

        Example:
            @AntiPetros clear_all_is_online_messages
        """
        await self.clear_all_is_online_messages_mechanism()
        await delete_message_if_text_channel(ctx)

    @ auto_meta_info_command(clear_invocation=True, experimental=True, logged=True)
    @ allowed_channel_and_allowed_role()
    async def server_notification_settings(self, ctx: commands.Context):
        await delete_message_if_text_channel(ctx)
        selection_question = AskSelection.from_context(ctx, timeout=300, delete_question=True, error_on=True)
        selection_question.set_title("Please select the settings you want to change")
        for option in ["notification timeout", "enable/disable status change report", "enable/disable is_online message", "is_online_messages_channel"]:
            selection_question.options.add_option(selection_question.option_item(option))
        answer = await selection_question.ask()

        if answer == "notification timeout":
            input_question = AskInput.from_other_asking(selection_question, delete_answers=True)
            input_question.description = f"Current timeout is **{self.notification_time_out} seconds**.\nPlease the new value in seconds you want to set!"
            input_question.validator(lambda x: x.isnumeric())
            notification_answer = await input_question.ask()
            COGS_CONFIG.set(self.config_name, "notification_time_out_seconds", str(notification_answer))
            await ctx.send(f"notification timeout has been set to {self.notification_time_out} seconds!", delete_after=120)
            return

        elif answer == "is_online_messages_channel":
            input_question = AskInput.from_other_asking(selection_question, delete_answers=True)
            input_question.description = f"Currently the is_online messages are posted in the channel {self.is_online_messages_channel.mention}(`{self.is_online_messages_channel.name}`).\n\nPlease enter the name of the channel you want to set this setting to!"
            input_question.validator = lambda x: x.casefold() in self.bot.channels_name_dict
            selected_channel_name = await input_question.ask()
            COGS_CONFIG.set(self.config_name, "is_online_messages_channel", selected_channel_name.casefold())
            await ctx.send(f"Channel for `is_online messages` has been set to {self.is_online_messages_channel.mention}(`{self.is_online_messages_channel.name}`!\n rebuilding `is_online messages` now!", delete_after=120)
            await self.clear_all_is_online_messages(ctx)
            await ctx.send("cleared all is online messages, resending with next loop iteration (max 2 min)", delete_after=120)
            return

        else:
            server_selection = AskSelection.from_other_asking(selection_question)
            server_selection.description = f"Please select the server for which you want to change the setting `{answer}`"
            for server in self.server_items:
                server_selection.options.add_option(server_selection.option_item(server))
            selected_server = await server_selection.ask()

        if answer == "enable/disable status change report":
            current_value = COGS_CONFIG.retrieve(self.config_name, f"{selected_server.name.lower()}_report_status_change", typus=bool, direct_fallback=False)
            current_value_text = "ENABLED" if current_value is True else "DISABLED"
            inverse_value_text = "DISABLE" if current_value is True else "ENABLE"
            inverse_set_value = "no" if current_value is True else "yes"
            confirm_question = AskConfirmation.from_other_asking(selection_question)

            confirm_question.description = f"The setting `status change report` is currently **{current_value_text}** for Server `{selected_server.pretty_name}`.\nDo you want to `{inverse_value_text}` it?"
            confirm_answer = await confirm_question.ask()
            if confirm_answer is confirm_question.ACCEPTED:
                COGS_CONFIG.set(self.config_name, f"{selected_server.name.lower()}_report_status_change", inverse_set_value)
                await ctx.send(f"The Server `{selected_server.pretty_name}` has the setting `status change report` now set to **{inverse_value_text}D**", delete_after=120)
                return
            else:
                raise AskCanceledError(confirm_question, confirm_answer)

        elif answer == "enable/disable is_online message":
            current_value = COGS_CONFIG.retrieve(self.config_name, f"{selected_server.name.lower()}_is_online_message_enabled", typus=bool, direct_fallback=True)
            current_value_text = "ENABLED" if current_value is True else "DISABLED"
            inverse_value_text = "DISABLE" if current_value is True else "ENABLE"
            inverse_set_value = "no" if current_value is True else "yes"
            confirm_question = AskConfirmation.from_other_asking(selection_question)

            confirm_question.description = f"The setting `show in is-online-message` is currently **{current_value_text}** for Server `{selected_server.pretty_name}`.\nDo you want to `{inverse_value_text}` it?"
            confirm_answer = await confirm_question.ask()
            if confirm_answer is confirm_question.ACCEPTED:
                COGS_CONFIG.set(self.config_name, f"{selected_server.name.lower()}_is_online_message_enabled", inverse_set_value)
                await ctx.send(f"The Server `{selected_server.pretty_name}` has the setting `show in is-online-message` now set to **{inverse_value_text}D**!\n rebuilding `is-online-messages` now!", delete_after=120)
                await self.clear_all_is_online_messages(ctx)
                await ctx.send("cleared all is online messages, resending with next loop iteration (max 2 min)", delete_after=120)
                return
            else:
                raise AskCanceledError(confirm_question, confirm_answer)

    @ auto_meta_info_command(only_debug=True, logged=True)
    @ owner_or_admin()
    async def debug_server_notification(self, ctx: commands.Context, server_name: str = "mainserver_1", new_prev_status: bool = False):
        server = await self._get_server_by_name(server_name)
        await server.status.add_new_status(ServerStatus(new_prev_status))
        await ctx.send(f"{server.pretty_name} is {server.current_status}", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
        await delete_message_if_text_channel(ctx)

    @ auto_meta_info_command(only_debug=True)
    @ owner_or_admin()
    async def tell_all_status(self, ctx: commands.Context):
        for server in self.server_items:
            if server.log_folder is not None:
                print(f"{server.name} | {server.newest_log_item.created}")
            await ctx.send(f"__***{server.name.upper()}***__ --> `{server.current_status}` -> __**Timeouts:**_ *ServerStatus.ON* = `{server.on_notification_timeout.get(ServerStatus.ON)}`, *ServerStatus.OFF* = `{server.on_notification_timeout.get(ServerStatus.OFF)}`")

    @ auto_meta_info_command(clear_invocation=True, logged=True)
    @ allowed_channel_and_allowed_role()
    async def add_mod_data(self, ctx: commands.Context, identifier: str, name: str, link: str):
        identifier = identifier.removeprefix('@')
        data = loadjson(APPDATA['mod_lookup.json'])
        if identifier in data:
            existing = f"@{identifier}=\n{indent(pformat(data.get(identifier)),'    ')}"
            await ctx.send(f'Mod already in stored mod-data:\n{CodeBlock(existing, "python")}', allowed_mentions=discord.AllowedMentions.none(), delete_after=90)
            return

        data[identifier] = {"name": name, "link": link}
        writejson(data, APPDATA['mod_lookup.json'])
        await ctx.send(f"`{identifier}` was added to the mod data")
        for server in self.server_items:
            try:
                server.log_parser.reset()
            except AttributeError:
                log.debug("Server Item %s has no Attribute 'log_parser'", server)

    @ auto_meta_info_command(clear_invocation=True)
    @ owner_or_admin()
    async def tell_amount_mod_data_requested(self, ctx: commands.Context):
        await ctx.send(f"Mod data was requested {self.amount_mod_data_requested} times", delete_after=120)

    @ auto_meta_info_command(clear_invocation=True)
    @ owner_or_admin()
    async def tell_amount_restart_requested(self, ctx: commands.Context):
        await ctx.send(f"Restart was requested {self.amount_restart_requested} times", delete_after=120)

    def _data_strip_population(self, timestamps: list[datetime], amounts: list[int]) -> Union[tuple[list[datetime], list[int]], None]:
        new_timestamps = []
        new_amounts = []
        for timestamp, amount in dropwhile(lambda x: x[1] <= 0, zip(timestamps, amounts)):
            new_timestamps.append(timestamp)
            new_amounts.append(amount)

        return new_timestamps, new_amounts

    @ auto_meta_info_command(experimental=True, confirm_command_received=True)
    @ allowed_channel_and_allowed_role()
    async def show_population(self, ctx: commands.Context):
        async with ctx.typing():
            interested_server = [server for server in self.server_items if server.name.casefold() not in {'testserver_2'}]

            cleaned_interested_server = []
            for_max = []
            for server in interested_server:
                _timestamps, _amounts = await general_db.get_server_population(server=server)
                if any(num > 0 for num in _amounts):
                    for_max += _amounts
                    cleaned_interested_server.append(server)
                await asyncio.sleep(0)
                max_y = max(for_max)

            sub_1 = 2
            sub_2 = int(math.ceil(len(cleaned_interested_server) / 2))

            plot_path_effects = (patheffects.SimpleLineShadow(), patheffects.Normal())
            text_path_effects = (patheffects.SimpleLineShadow(), patheffects.Stroke(linewidth=2 / len(cleaned_interested_server), foreground="white"), patheffects.Normal())

            fig, axs = plt.subplots(sub_2, sub_1, sharey=True)
            fig.suptitle("Server Population", fontsize=80 / (len(cleaned_interested_server) / 2))
            for sub_ax, server in zip(axs.flat, cleaned_interested_server):

                timestamps, amounts = await general_db.get_server_population(server=server)
                timestamps, amounts = await asyncio.to_thread(self._data_strip_population, timestamps=timestamps, amounts=amounts)

                notation_color = "white"
                spine_color = "white"

                sub_ax.plot(timestamps, amounts, linewidth=0.25,
                            color=rgb256_to_rgb1((0.75, 0.75, 0.75, 0.01)),
                            solid_joinstyle='round',
                            solid_capstyle='round',
                            antialiased=True,
                            snap=True)
                locator = mdates.AutoDateLocator()
                formatter = mdates.ConciseDateFormatter(locator)
                sub_ax.xaxis.set_major_locator(locator)
                sub_ax.xaxis.set_major_formatter(formatter)

                sub_ax.xaxis.label.set_color(spine_color)

                sub_ax.yaxis.label.set_color(spine_color)

                sub_ax.spines['bottom'].set_color(spine_color)
                sub_ax.spines['top'].set_color(spine_color)
                sub_ax.spines['right'].set_color(spine_color)
                sub_ax.spines['left'].set_color(spine_color)

                sub_ax.tick_params(axis='x', colors=spine_color, labelsize=20 / (len(cleaned_interested_server) / 2))
                sub_ax.tick_params(axis='y', colors=spine_color, labelsize=20 / (len(cleaned_interested_server) / 2))
                sub_ax.title.set_color(notation_color)

                color = list(self.bot.colors.get(server.color.casefold()).rgb_norm)
                color.append(0.75)

                sub_ax.fill_between(timestamps, amounts, color=color, linewidth=0)

                # sub_ax.set_ylabel('Amount Players', fontsize=30 / len(cleaned_interested_server))

                sub_ax.set_title(f"{server.pretty_name}", fontsize=40 / (len(cleaned_interested_server) / 2))
                sub_ax.set_ylim(0, max_y)
                await asyncio.sleep(0)
            fig.tight_layout()

            await asyncio.sleep(0)
            with BytesIO() as bytefile:
                fig.savefig(bytefile, format='png', dpi=100 * len(cleaned_interested_server))

                bytefile.seek(0)

                file = discord.File(bytefile, 'servers_pop.png')
            await ctx.send(file=file)


# endregion [Commands]


# region [HelperMethods]


    async def add_to_amount_mod_data_requested(self, amount_to_add: int = 1):
        async with self.add_amount_lock:
            self.amount_mod_data_requested = self.amount_mod_data_requested + amount_to_add

    async def add_to_amount_restart_requested(self, amount_to_add: int = 1):
        async with self.add_amount_lock:
            self.amount_restart_requested = self.amount_restart_requested + amount_to_add

    async def clear_all_is_online_messages_mechanism(self):
        self.halt_is_online_update = True
        if self.is_online_message_loop.is_running() is True:
            self.is_online_message_loop.stop()
        while self.is_online_message_loop.is_running() is True:
            await asyncio.sleep(1)

        await self.is_online_header_message.remove()
        await asyncio.gather(*[server.is_online_message.remove() for server in self.server_items])

        if self.is_online_message_loop.is_running() is False:
            self.is_online_message_loop.start()
        await asyncio.sleep(5)
        self.halt_is_online_update = False

    async def _recreate_all_is_online_messages(self):
        await self.clear_all_is_online_messages_mechanism()
        await self._create_status_header_message()
        for server in self.server_items:
            await server.is_online_message.update()

    async def _handle_restart_request(self, member: discord.Member, server_item: ServerItem):
        reasons = ["Performance", "Mass disconnects", "HC disconnected", "Other"]
        channel = await self.bot.ensure_dm_channel(member)
        if server_item.last_restart_request_received is not None and server_item.last_restart_request_received + timedelta(minutes=5) >= datetime.now(tz=timezone.utc):
            await channel.send('Already received a restart request in the last 5 min')
            return
        ask_selection = AskSelection(author=member, channel=channel, delete_question=True, error_on=True)
        ask_selection.set_title("Reason for Restart?")
        for reason in reasons:
            ask_selection.options.add_option(AskSelectionOption(item=reason))
        reason_answer = await ask_selection.ask()
        if reason_answer == "Other":
            ask_input = AskInput.from_other_asking(ask_selection, delete_answers=True)
            ask_input.set_title("Please specify the reason briefly")
            reason_answer = await ask_input.ask()

        saved_ask = AskConfirmation.from_other_asking(ask_selection)
        saved_ask.set_title("Has the commander saved already and did the save complete Message pop up?")
        saved_answer = await saved_ask.ask()

        ready_ask = AskConfirmation.from_other_asking(saved_ask)
        ready_ask.set_title("Is everyone on the server ready for the restart?")
        ready_answer = await ready_ask.ask()

        confirm_ask = AskConfirmation.from_other_asking(ask_selection)
        confirm_ask.set_title("Do you want to send this restart request?")
        confirm_answer = await confirm_ask.ask()
        if confirm_answer is confirm_ask.DECLINED:
            await channel.send('Canceled!')
            return
        await channel.send('Contacting an admin now for the restart, he will then contact you. Please be patient!')
        if server_item.last_restart_request_received is not None and server_item.last_restart_request_received + timedelta(minutes=self.restart_request_timeout) >= datetime.now(tz=timezone.utc):
            await channel.send('Already received a restart request in the last 5 min')
            return
        now = datetime.now(tz=timezone.utc)
        server_item.last_restart_request_received = now
        fields = [self.bot.field_item(name="Reason given", value=CodeBlock(reason_answer, 'fixx'), inline=False),
                  self.bot.field_item(name="Game is Saved?", value="yes" if saved_answer is AskConfirmation.ACCEPTED else "no", inline=False),
                  self.bot.field_item(name="Everyone on Server ready for Restart?", value="yes" if ready_answer is AskConfirmation.ACCEPTED else 'no', inline=False)]
        last_restarted_pretty = await server_item.get_last_restarted_at_pretty()

        fields.append(self.bot.field_item(name="Last Restarted", value=str(last_restarted_pretty), inline=False))

        embed_data = await self.bot.make_generic_embed(title=f'Restart was Requested for Server {server_item}',
                                                       description=f"Requested by {member.mention} (`{member}`)",
                                                       url=server_item.battle_metrics_url,
                                                       timestamp=now,
                                                       fields=fields,
                                                       thumbnail=server_item.thumbnail,
                                                       color=server_item.color)

        notify_dict = self.request_restart_to_notify
        for notify_channel in notify_dict.get('channels', []):
            await notify_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        for notify_member in notify_dict.get('members', []):
            await notify_member.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

        for notify_webhook in notify_dict.get('webhooks', []):
            await notify_webhook.send(**embed_data, username="Restar Request", avatar_url=server_item.thumbnail, allowed_mentions=discord.AllowedMentions.none())

    async def _get_log_by_time(self, server_item: ServerItem, timestamp: datetime) -> discord.File:
        timestamp = timestamp.astimezone(timezone.utc)
        for log_item in server_item.log_items:
            if log_item.created < timestamp > log_item.modified:
                with BytesIO() as bytefile:
                    async for chunk in await log_item.content_iter():
                        bytefile.write(chunk)
                    bytefile.seek(0)
                    return discord.File(bytefile, log_item.name)
            await asyncio.sleep(0)

    async def _server_from_is_online_message_id(self, is_online_message_id: int) -> ServerItem:
        server_name = await self.db.get_server_name_from_is_online_message_id(is_online_message_id=is_online_message_id)
        return {server.name.casefold(): server for server in self.server_items}.get(server_name.casefold())

    async def _get_server_by_name(self, server_name: str):
        server = {server_item.name.casefold(): server_item for server_item in self.server_items}.get(server_name.casefold(), None)
        if server is None:
            server_name = fuzzprocess.extractOne(server_name.casefold(), [server_item.name.casefold() for server_item in self.server_items])[0]
            server = await self._get_server_by_name(server_name)
        return server

    async def send_server_notification(self, server_item: ServerItem, changed_to: ServerStatus):
        log.debug("sending server status change notfication for server %s, changed to %s", server_item.name, changed_to)
        title = server_item.pretty_name

        description = "was switched __***ON***__" if changed_to is ServerStatus.ON else "was switched __***OFF***__"
        thumbnail = self.server_logos.get(server_item.name.casefold(), self.server_symbol)
        now = datetime.now(timezone.utc)
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=description,
                                                       timestamp=now,
                                                       thumbnail=thumbnail,
                                                       typus="server_notification_embed",
                                                       fields=[self.bot.field_item(name="UTC", value=f"`{now.strftime('%Y-%m-%d %H:%M:%S')}`", inline=False),
                                                               self.bot.field_item(name="Your Timezone", value="`⇓ See Timestamp ⇓`", inline=False)])

        channel = self.notification_channel
        msg = await channel.send(**embed_data)

        self.latest_sever_notification_msg_id = msg.id

    async def _load_server_items_helper(self, server_name: str):
        log.debug("Starting to load '%s'", server_name)
        server_adress = COGS_CONFIG.retrieve(self.config_name, f"{server_name.lower()}_address", typus=str, direct_fallback=None)
        if not server_adress:
            log.critical("Missing server address for server %s", server_name)
            return None
        log_folder = server_name
        if COGS_CONFIG.retrieve(self.config_name, f"{server_name.lower()}_exclude_logs", typus=bool, direct_fallback=False) is True:
            log_folder = None
        server_item = ServerItem(server_name, server_adress, log_folder)
        asyncio.create_task(self.db.insert_server(server_item=server_item))

        asyncio.create_task(server_item.is_online())

        await (server_item.gather_log_items())
        await server_item.retrieve_is_online_message()

        asyncio.create_task(delayed_execution(10, server_item.get_mod_files))
        return server_item

    async def load_server_items(self):

        ServerItem.cog = self
        ServerItem.status_switch_signal.connect(self.send_server_notification)
        await ServerItem.ensure_client()
        _out = []
        for server_item in [await self._load_server_items_helper(name) for name in self.server_names]:
            if server_item is not None:
                _out.append(server_item)

        self.server_items = sorted(_out, key=lambda x: x.priority)
        log.debug("finished loading server items")
        return self.server_items

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
