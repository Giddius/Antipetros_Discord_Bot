# region [Imports]

# * Standard Library Imports -->
import os
from datetime import datetime
from collections import namedtuple
import traceback
import asyncio
from asyncio import Future, wait_for
from contextlib import suppress
import sys
from pprint import pprint, pformat
from inspect import iscoroutinefunction, iscoroutine, getmro, getsource, getmembers
import time
# * Third Party Imports -->
from discord.ext import commands, tasks
import discord

from async_property import async_property
from discord import Embed, File
from watchgod import awatch, DefaultDirWatcher, Change
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from udpy import AsyncUrbanClient
import pyowm
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.engine.special_prefix import when_mentioned_or_roles_or
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, readit, writeit
from antipetros_discordbot.utility.misc import sync_to_async, save_bin_file
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.named_tuples import CreatorMember
from antipetros_discordbot.command_staff.staff_invoke_statistician import InvokeStatistician
from antipetros_discordbot.command_staff.staff_error_handler import ErrorHandler
from antipetros_discordbot.engine.global_checks import user_not_blacklisted
from antipetros_discordbot.command_staff import CommandStaffRoster, ErrorHandler, InvokeStatistician, TimeKeeper, ChannelStatistician, RegexKeeper, ColorKeeper
# endregion[Imports]


# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

# TODO: create regions for this file
# TODO: Document and Docstrings
# IDEA: Use an assistant class to hold some of the properties and then use the __getattr__ to make it look as one object, just for structuring


class AntiPetrosBot(commands.Bot):
    creator = CreatorMember('Giddi', 576522029470056450, None, None)
    executor = ThreadPoolExecutor(6, thread_name_prefix='Bot_Thread')
    admin_cog_import_path = "antipetros_discordbot.cogs.admin_cogs.admin_cog"
    bot_feature_suggestion_folder = APPDATA["bot_feature_suggestion_data"]
    bot_feature_suggestion_json_file = APPDATA['bot_feature_suggestions.json']
    cog_import_base_path = BASE_CONFIG.get('general_settings', 'cogs_location')

    available_staff = (InvokeStatistician, ErrorHandler, TimeKeeper, ChannelStatistician, RegexKeeper, ColorKeeper)

    def __init__(self, help_invocation='help', ** kwargs):
        super().__init__(owner_id=self.creator.id, case_insensitive=BASE_CONFIG.getboolean('command_settings', 'invocation_case_insensitive'), **kwargs)
        self.help_invocation = help_invocation
        self.description = readit(APPDATA['bot_description.md'])
        self.command_staff = CommandStaffRoster(self, self.available_staff)
        self.general_data = loadjson(APPDATA['general_data.json'])
        self.max_message_length = 1900
        self.commands_executed = 0
        self.bot_member = None
        self.aio_request_session = None
        self.urban_client = None
        self.all_bot_roles = None
        self.current_day = datetime.utcnow().day
        self.clients_to_close = []

        user_not_blacklisted(self, log)

        self._setup()

        glog.class_init_notification(log, self)
        if self.is_debug:
            log.warning('!!!!!!!!!!!!!!!!! DEBUG MODE !!!!!!!!!!!!!!!!!')

    def _setup(self):
        self._get_initial_cogs()
        self.update_check_loop.start()

    async def on_ready(self):
        log.info('%s has connected to Discord!', self.user.name)
        await self._get_bot_info()
        await self._start_sessions()
        await self.wait_until_ready()
        await asyncio.sleep(2)
        await self.command_staff.staff_memo(attribute_name='if_ready')
        await self.to_all_cogs('on_ready_setup')
        if self.is_debug:
            await self.debug_function()
        if BASE_CONFIG.getboolean('startup_message', 'use_startup_message') is True:
            await self.send_startup_message()
        await self._watch_for_shutdown_trigger()

    async def _watch_for_shutdown_trigger(self):
        async for changes in awatch(APPDATA['shutdown_trigger'], loop=self.loop):
            for change_typus, change_path in changes:
                if change_typus is Change.added:
                    name, extension = os.path.basename(change_path).split('.')
                    if extension.casefold() == 'trigger':
                        if name.casefold() == 'shutdown':
                            await self.close()
                        elif name.casefold() == 'emergency_shutdown':
                            sys.exit()

    async def on_message(self, message: discord.Message) -> None:
        await self.command_staff.record_channel_usage(message)
        await self.process_commands(message)

    async def send_startup_message(self):
        channel = self.get_channel(BASE_CONFIG.getint('startup_message', 'channel'))
        msg = BASE_CONFIG.get('startup_message', 'message')
        delete_time = 240 if self.is_debug is True else 600
        await channel.send(msg, delete_after=delete_time)

    async def to_all_cogs(self, command, *args, **kwargs):
        for cog_name, cog_object in self.cogs.items():
            if hasattr(cog_object, command):
                await getattr(cog_object, command)(*args, **kwargs)

    async def _get_bot_info(self):
        if self.all_bot_roles is None:
            self.all_bot_roles = []
            self.bot_member = await self.retrieve_member(self.antistasi_guild.id, self.id)
            for index, role in enumerate(self.bot_member.roles):
                if index != 0:
                    self.all_bot_roles.append(role)
        self.command_prefix = BASE_CONFIG.get('prefix', 'command_prefix')
        if BASE_CONFIG.getboolean('prefix', 'invoke_by_role_and_mention') is True:
            self.command_prefix = when_mentioned_or_roles_or(BASE_CONFIG.get('prefix', 'command_prefix'))

        AntiPetrosBot.creator = self.creator._replace(**{'member_object': await self.retrieve_antistasi_member(self.creator.id), 'user_object': await self.fetch_user(self.creator.id)})

    async def _start_sessions(self):
        if self.aio_request_session is None:
            self.aio_request_session = aiohttp.ClientSession(loop=self.loop)
            self.clients_to_close.append(self.aio_request_session)
            log.debug("'%s' was started", str(self.aio_request_session))
        if self.urban_client is None:
            self.urban_client = AsyncUrbanClient(self.aio_request_session)
            log.debug("'%s' was started", str(self.urban_client))

    def _get_initial_cogs(self):
        self.load_extension(self.admin_cog_import_path)
        log.debug("loaded extension\cog: '%s' from '%s'", self.admin_cog_import_path.split('.')[-1], self.admin_cog_import_path)
        for _cog in BASE_CONFIG.options('extensions'):
            if BASE_CONFIG.getboolean('extensions', _cog) is True:
                name = _cog.split('.')[-1]
                full_import_path = self.cog_import_base_path + '.' + _cog
                self.load_extension(full_import_path)
                log.debug("loaded extension-cog: '%s' from '%s'", name, full_import_path)

        log.info("extensions-cogs loaded: %s", ', '.join(self.cogs))

    async def close(self):
        log.info("shutting down bot loops")
        self.update_check_loop.stop()

        log.info("retiring troops")
        self.command_staff.retire_troops()

        log.info("shutting down executor")
        self.executor.shutdown()
        for session in self.clients_to_close:
            await session.close()
            log.info("'%s' was shut down", str(session))
        log.debug('aiosession closed: %s', str(self.aio_request_session.closed))

        log.info("closing bot")
        await self.wait_until_ready()
        await super().close()
        time.sleep(2)

    @staticmethod
    def activity_from_config(option='standard_activity'):
        activity_dict = {'playing': discord.ActivityType.playing,
                         'watching': discord.ActivityType.watching,
                         'listening': discord.ActivityType.listening,
                         'streaming': discord.ActivityType.streaming}
        text, activity_type = BASE_CONFIG.getlist('activity', option)
        if activity_type not in activity_dict:
            log.critical("'%s' is not an Valid ActivityType, aborting activity change")
            return
        activity_type = activity_dict.get(activity_type)

        return discord.Activity(name=text, type=activity_type)

    async def on_command_error(self, ctx, error):
        await self.command_staff.handle_errors(ctx, error, traceback.format_exc())

    @tasks.loop(minutes=5, reconnect=True)
    async def update_check_loop(self):
        if self.current_day == datetime.utcnow().day:
            return
        self.current_day = datetime.utcnow().day
        await self.command_staff.staff_memo('update')
        await self.to_all_cogs('updated')

    @update_check_loop.before_loop
    async def before_update_check_loop(self):
        await self.wait_until_ready()

    def all_cog_commands(self):
        for cog_name, cog_object in self.cogs.items():
            for command in cog_object.get_commands():
                yield command

    @property
    def antistasi_guild(self):
        return self.get_guild(self.general_data.get('antistasi_guild_id'))

    @property
    def id(self):
        return self.user.id

    @property
    def display_name(self):
        return self.user.display_name

    @property
    def is_debug(self):
        return BASE_CONFIG.getboolean('general_settings', 'is_debug')

    @property
    def blacklisted_users(self):
        return loadjson(APPDATA['blacklist.json'])

    @property
    def notify_contact_member(self):
        return BASE_CONFIG.get('blacklist', 'notify_contact_member')

    @property
    def std_date_time_format(self):
        return "%Y-%m-%d %H:%M:%S"

    @property
    def shutdown_command(self):
        return self.get_command('shutdown')

    def blacklisted_user_ids(self):
        for user_item in self.blacklisted_users:
            yield user_item.get('id')

    async def message_creator(self, message=None, embed=None, file=None):
        if message is None and embed is None:
            message = 'message has no content'
        await self.creator.member_object.send(content=message, embed=embed, file=file)

    async def retrieve_antistasi_member(self, user_id):
        return await self.antistasi_guild.fetch_member(user_id)

    async def retrieve_member(self, guild_id, user_id):
        guild = self.get_guild(guild_id)
        return await guild.fetch_member(user_id)

    async def split_to_messages(self, ctx, message, split_on='\n', in_codeblock=False):
        _out = ''
        chunks = message.split(split_on)
        for chunk in chunks:
            if sum(map(len, _out)) + len(chunk + split_on) < self.max_message_length:
                _out += chunk + split_on
            else:
                if in_codeblock is True:
                    _out = f"```json\n{_out}\n```"
                await ctx.send(_out)
                await asyncio.sleep(0.5)
                _out = ''
        if in_codeblock is True:
            _out = f"```json\n{_out}\n```"
        await ctx.send(_out)

    @sync_to_async
    def channel_from_name(self, channel_name):
        return discord.utils.get(self.antistasi_guild.channels, name=channel_name)

    @sync_to_async
    def member_by_name(self, member_name):
        member_name = member_name.casefold()
        for member in self.antistasi_guild.members:

            if member.name.casefold() == member_name:
                return member

    async def execute_in_thread(self, func, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, func, *args, **kwargs)

    async def save_feature_suggestion_extra_data(self, data_name, data_content):
        path = pathmaker(self.bot_feature_suggestion_folder, data_name)
        await self.execute_in_thread(save_bin_file, path, data_content)
        return path

    async def add_to_feature_suggestions(self, item):
        feat_suggest_json = loadjson(self.bot_feature_suggestion_json_file)
        feat_suggest_json.append(item._asdict())
        writejson(feat_suggest_json, self.bot_feature_suggestion_json_file)

    async def debug_function(self):
        log.debug("debug function triggered")
        path = pathmaker(APPDATA['debug'], 'general_debug')
        extension = 'json'
        _out = []

        writejson(_out, path + '.' + extension)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.__class__.__name__
