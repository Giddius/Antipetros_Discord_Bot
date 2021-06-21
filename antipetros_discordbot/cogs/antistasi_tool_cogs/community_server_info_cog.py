
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
# * Third Party Imports -->
import a2s
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
from fuzzywuzzy import process as fuzzprocess
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel, loop_starter
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, log_invoker, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command, auto_meta_info_group
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, ListMarker
from antipetros_discordbot.auxiliary_classes.server_item import ServerItem, ServerStatus
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.emoji_handling import NUMERIC_EMOJIS, ALPHABET_EMOJIS, CHECK_MARK_BUTTON_EMOJI, CHECK_MARK_BUTTON_EMOJI, CROSS_MARK_BUTTON_EMOJI
from collections import deque
from antipetros_discordbot.utility.exceptions import TokenMissingError, AskCanceledError
from antipetros_discordbot.auxiliary_classes.asking_items import AskConfirmation, AskFile, AskInput, AskInputManyAnswers, AskAnswer, AskSelectionOptionsMapping, AskSelectionOption, AskSelection


if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
import re
from io import BytesIO
from antipetros_discordbot.utility.sqldata_storager import general_db
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
                                            'notification_time_out_seconds': 0}}

    server_logos = {'mainserver_1': "https://i.postimg.cc/d0Y0krSc/mainserver-1-logo.png",
                    "mainserver_2": "https://i.postimg.cc/BbL8csTr/mainserver-2-logo.png"}

    available_server_options = {"report_status_change": "no",
                                "show_in_server_command": "no",
                                "is_online_message_enabled": "no",
                                "exclude_logs": "yes"}
    battlemetrics_api_base_url = "https://api.battlemetrics.com/"

    reason_keyword_identifier = '%'

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.server_items = self.load_server_items()
        self.color = 'yellow'
        self.latest_sever_notification_msg_id = None
        self.amount_mod_data_requested = 0

        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


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
    def is_online_messages(self) -> dict:
        return loadjson(self.is_online_messages_data_file)

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
# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await super().on_ready_setup()
        await asyncio.gather(*[general_db.insert_server(server) for server in self.server_items])
        await ServerItem.ensure_client()
        for loop_object in self.loops.values():
            loop_starter(loop_object)

        for server in self.server_items:
            await server.is_online()
        await asyncio.gather(*[server.gather_log_items() for server in self.server_items])

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await ServerItem.ensure_client()
        if UpdateTypus.CONFIG in typus:
            self.server_items = self.load_server_items()
        await super().update(typus)
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

    @tasks.loop(minutes=5, seconds=30, reconnect=True)
    async def update_logs_loop(self):
        if any([self.ready, self.bot.setup_finished]) is False:
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

    @tasks.loop(minutes=1, reconnect=True)
    async def is_online_message_loop(self):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        await asyncio.gather(*[server.is_online() for server in self.server_items])
        if datetime.now(tz=timezone.utc).minute % 2 == 0:
            for server in self.server_items:
                if server.is_online_message_enabled is True:
                    await self._update_is_online_messages(server)
                else:
                    await self._delete_is_online_message(server)
            log.info("Updated 'is_online_messages'")
# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def is_online_mod_list_reaction_listener(self, payload: discord.RawReactionActionEvent):
        """
        Listens to emojis being clicked on the `is_online` messages to then send the user that clicked it, the modlist per DM.

        Removes all other emojis being assigned to the messages.

        """
        if self.completely_ready is False:
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

        if payload.emoji != self.bot.armahosts_emoji:
            asyncio.create_task(message.remove_reaction(payload.emoji, reaction_member))
            asyncio.create_task(self.clear_emojis_from_is_online_message())
            return

        server_item = await self._server_from_is_online_message_id(message.id)
        if server_item.current_status is ServerStatus.OFF or server_item.log_folder is None:
            asyncio.create_task(message.remove_reaction(payload.emoji, reaction_member))
            return

        await self._send_to_dm(reaction_member, server_item)
        self.amount_mod_data_requested += 1
        await asyncio.sleep(0)
        await message.remove_reaction(payload.emoji, reaction_member)

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

    @auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS], aliases=['get_logs'])
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
            await asyncio.sleep(2)

    @auto_meta_info_command(categories=[CommandCategory.DEVTOOLS, CommandCategory.ADMINTOOLS], experimental=True)
    @allowed_channel_and_allowed_role()
    async def only_log_level(self, ctx: commands.Context, level: str = 'error'):
        server = await self._get_server_by_name('mainserver_1')
        text = await server.log_parser.get_only_level(level)
        with BytesIO() as bytefile:
            bytefile.write(text.encode('utf-8', errors='ignore'))
            bytefile.seek(0)
            file = discord.File(bytefile, f'only_level_{level}.log')
        await ctx.send(file=file)

    @auto_meta_info_command(aliases=['restart_reason'], categories=[CommandCategory.ADMINTOOLS])
    @owner_or_admin()
    @log_invoker(log, "info")
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
        embed.clear_fields()
        embed.add_field(name='Reason', value=CodeBlock(reason, 'fix'), inline=False)
        embed.add_field(name='Reason set by', value=f"{ctx.author.mention} at `{datetime.now(tz=timezone.utc).strftime(self.bot.std_date_time_format)} UTC`", inline=False)
        embed.add_field(name="Server Status change happend at", value="⇓ See Timestamp (`in your local timezone`) ⇓", inline=False)
        server = await self._get_server_by_name(embed.title)
        log_file = await self._get_log_by_time(server, embed.timestamp)

        await msg.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none(), file=log_file)
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(categories=[CommandCategory.ADMINTOOLS])
    @owner_or_admin()
    @log_invoker(log, "info")
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

    @auto_meta_info_command(categories=[CommandCategory.ADMINTOOLS])
    @owner_or_admin()
    async def list_stored_restart_reasons(self, ctx: commands.Context):
        fields = [self.bot.field_item(name=name.strip(self.reason_keyword_identifier), value=CodeBlock(value, 'fix'), inline=False) for name, value in self.stored_reasons.items()]
        title = "Stored Restart Reasons"
        description = f"To use the reason, prefix them with `{self.reason_keyword_identifier}` (no space in between).\nExample: `{self.reason_keyword_identifier}disconnect`"
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title=title, description=description, fields=fields, thumbnail=None):
            await ctx.author.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command()
    @owner_or_admin()
    async def clear_all_is_online_messages(self, ctx: commands.Context):
        """
        Clears all the `is_online` messages, so they can be rebuilt on the next loop.

        Example:
            @AntiPetros clear_all_is_online_messages
        """
        self.is_online_message_loop.stop()
        while self.is_online_message_loop.is_running() is True:
            await asyncio.sleep(5)
        await asyncio.gather(*[self._delete_is_online_message(server) for server in self.server_items])
        await delete_message_if_text_channel(ctx)
        self.is_online_message_loop.start()

    @auto_meta_info_command(clear_invocation=True, experimental=True)
    @owner_or_admin()
    @log_invoker(log, 'warning')
    async def server_notification_settings(self, ctx: commands.Context):
        await delete_message_if_text_channel(ctx)
        selection_question = AskSelection.from_context(ctx, timeout=300, delete_question=True, error_on=True)
        selection_question.description = "Please select the settings you want to change"
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

    @auto_meta_info_command(only_debug=True)
    @owner_or_admin()
    async def debug_server_notification(self, ctx: commands.Context, server_name: str = "mainserver_1", new_prev_status: bool = False):
        server = await self._get_server_by_name(server_name)
        server.status.add_new_status(ServerStatus(new_prev_status))
        await ctx.send(f"{server.pretty_name} is {server.current_status}", allowed_mentions=discord.AllowedMentions.none(), delete_after=60)
        await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(only_debug=True)
    @owner_or_admin()
    async def tell_all_status(self, ctx: commands.Context):
        for server in self.server_items:
            await ctx.send(f"{server.name} --> {server.current_status} -> Timeouts: ServerStatus.ON = {server.on_notification_timeout.get(ServerStatus.ON)}, ServerStatus.OFF = {server.on_notification_timeout.get(ServerStatus.OFF)}")

    @auto_meta_info_command()
    @owner_or_admin()
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
        await delete_message_if_text_channel(ctx, 30)
        for server in self.server_items:
            try:
                server.log_parser.reset()
            except AttributeError:
                log.debug("Server Item %s has not Attribute 'log_parser'", server)

    @auto_meta_info_command(clear_invocation=True)
    @owner_or_admin()
    async def tell_amount_mod_data_requested(self, ctx: commands.Context):
        await ctx.send(f"Mod data was requested {self.amount_mod_data_requested} times", delete_after=120)

# endregion [Commands]


# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

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
        except IndexError as e:
            log.error(e, exc_info=True)
            log.warning("Requesting log files to dm lead to an IndexError with Server %s", server.name)

            asyncio.create_task(server.gather_log_items())
            await member.send("Sorry there was an Error in getting the Mod data, please try again in a minute or so", allowed_mentions=discord.AllowedMentions.none())

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
                                                       fields=[self.bot.field_item(name="Server Status change happend at", value="⇓ See Timestamp(`Your local time`) ⇓", inline=False)])

        channel = self.notification_channel
        msg = await channel.send(**embed_data)

        self.latest_sever_notification_msg_id = msg.id

    async def _make_is_online_embed(self, server: ServerItem):
        description = ZERO_WIDTH
        if server.current_status is ServerStatus.OFF:
            description = 'is ***OFFLINE***'
        elif server.log_folder is not None:
            description = f"Click the {self.bot.armahosts_emoji} emoji to get the current Mod List."

        color = 'green' if server.current_status is ServerStatus.ON else 'red'
        thumbnail = self.server_logos.get(server.name.casefold(), self.server_symbol) if server.current_status is ServerStatus.ON else self.server_symbol_off
        fields = []
        if server.current_status is ServerStatus.ON:
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
                log.warning("is online message not found for server %s", server.name)
            data = self.is_online_messages.copy()
            try:
                del data[server.name.casefold()]
                writejson(data, self.is_online_messages_data_file)
            except Exception as e:
                log.error(e, exc_info=True)

    async def _create_is_online_message(self, server: ServerItem):
        embed_data = await self._make_is_online_embed(server)
        msg = await self.is_online_messages_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        if server.log_folder is not None and server.current_status is ServerStatus.ON:
            await msg.add_reaction(self.bot.armahosts_emoji)
        else:
            await self._clear_emoji_from_msg(msg.id, True)
        is_online_data = self.is_online_messages
        is_online_data[server.name.casefold()] = msg.id
        writejson(is_online_data, self.is_online_messages_data_file)

    async def _update_is_online_messages(self, server: ServerItem):
        try:
            message_id = self.is_online_messages.get(server.name.casefold())
            if message_id is None:
                await self._create_is_online_message(server)
                return
            msg = await self.is_online_messages_channel.fetch_message(message_id)
            embed_data = await self._make_is_online_embed(server)
            await msg.edit(**embed_data, allowed_mentions=discord.AllowedMentions.none())
            await self.clear_emojis_from_is_online_message()
            if server.current_status is ServerStatus.ON and server.log_folder is not None:
                await msg.add_reaction(self.bot.armahosts_emoji)
            else:
                await self._clear_emoji_from_msg(msg.id, True)
        except discord.errors.NotFound as e:
            log.warning("is_online_message for server %s not found!", server)

            data = self.is_online_messages.copy()
            data.pop(server.name.casefold(), None)
            writejson(data, self.is_online_messages_data_file)

    async def clear_emojis_from_is_online_message(self):
        for key, msg_id in self.is_online_messages.items():
            try:
                await self._clear_emoji_from_msg(msg_id)
            except discord.errors.NotFound as e:
                log.warning("is_online_message %s not found!", msg_id)
                data = self.is_online_messages.copy()
                data.pop(key, None)
                writejson(data, self.is_online_messages_data_file)

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
            log.warning("is_online_message %s not found!", msg_id)

    def load_server_items(self):
        ServerItem.cog = self
        ServerItem.status_switch_signal.connect(self.send_server_notification)
        ServerItem.update_is_online_message_signal.connect(self._update_is_online_messages)
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
