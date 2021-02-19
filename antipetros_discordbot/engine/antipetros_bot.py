"""
Actual Bot class.

"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
import time
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Union, TYPE_CHECKING, List, Set, Tuple
import random
from webdav3.client import Client
# * Third Party Imports --------------------------------------------------------------------------------->
import aiohttp
import discord
from udpy import AsyncUrbanClient
from watchgod import Change, awatch
from discord.ext import tasks, commands
import arrow
from humanize import naturaltime

from icecream import ic

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import save_bin_file, sync_to_async
from antipetros_discordbot.engine.global_checks import user_not_blacklisted
from antipetros_discordbot.utility.checks import owner_or_admin
from antipetros_discordbot.utility.named_tuples import CreatorMember
from antipetros_discordbot.engine.special_prefix import when_mentioned_or_roles_or
from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
from antipetros_discordbot.utility.gidtools_functions import readit, loadjson, pathmaker, writejson, pickleit, get_pickled
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.emoji_handling import normalize_emoji
from antipetros_discordbot.cogs import BOT_ADMIN_COG_PATHS, DISCORD_ADMIN_COG_PATHS, DEV_COG_PATHS
# endregion[Imports]


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
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

# TODO: create regions for this file
# TODO: Document and Docstrings


class AntiPetrosBot(commands.Bot):

    # region [ClassAttributes]

    creator = CreatorMember('Giddi', 576522029470056450, None, None)
    executor = ThreadPoolExecutor(6, thread_name_prefix='Bot_Thread')
    discord_admin_cog_import_path = "antipetros_discordbot.cogs.discord_admin_cogs.discord_admin_cog"
    bot_feature_suggestion_folder = APPDATA["bot_feature_suggestion_data"]
    bot_feature_suggestion_json_file = APPDATA['bot_feature_suggestions.json']
    essential_cog_paths = BOT_ADMIN_COG_PATHS + DISCORD_ADMIN_COG_PATHS
    dev_cog_paths = DEV_COG_PATHS

# endregion[ClassAttributes]

    def __init__(self, help_invocation='help', token=None, is_test=False, ** kwargs):

        # region [Init]
        super().__init__(owner_ids={self.creator.id, 413109712695984130, 122348088319803392},
                         case_insensitive=BASE_CONFIG.getboolean('command_settings', 'invocation_case_insensitive'),
                         self_bot=False,
                         command_prefix='$$',
                         activity=self.activity_from_config(),
                         intents=self.get_intents(),
                         ** kwargs)
        self.token = token
        self.help_invocation = help_invocation
        self.description = readit(APPDATA['bot_description.md'])
        self.support = BotSupporter(self)
        self.max_message_length = 1900
        self.commands_executed = 0
        self.bot_member = None
        self.aio_request_session = None
        self.all_bot_roles = None
        self.current_day = datetime.utcnow().day
        self.clients_to_close = []
        self.on_command_error = None
        self.github_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot"
        self.used_startup_message = None

        self.support.recruit_subsupports()
        user_not_blacklisted(self, log)
        if is_test is False:
            self._setup()

        glog.class_init_notification(log, self)

        # endregion[Init]

    def get_intents(self):

        if BASE_CONFIG.get('intents', 'convenience_setting') == 'all':
            intents = discord.Intents.all()
        elif BASE_CONFIG.get('intents', 'convenience_setting') == 'default':
            intents = discord.Intents.default()
        else:
            intents = discord.Intents.none()
            for sub_intent in BASE_CONFIG.options('intents'):
                if sub_intent != "convenience_setting":
                    setattr(intents, sub_intent, BASE_CONFIG.getboolean('intents', sub_intent))
        return intents

    def run(self, **kwargs):
        if self.token is None:
            raise RuntimeError("Discord Token is None")
        super().run(self.token, bot=True, reconnect=True, **kwargs)

    def _setup(self):
        self._get_initial_cogs()
        self.update_check_loop.start()

    async def create_doc_json(self):
        prefixes_list = []
        prefixes = BASE_CONFIG.getlist('prefix', 'command_prefix')
        role_exceptions = BASE_CONFIG.getlist('prefix', 'invoke_by_role_exceptions')
        extra = prefixes
        for role in self.all_bot_roles:
            if role.name not in role_exceptions and role.name.casefold() not in role_exceptions:  # and role.mentionable is True:
                prefixes_list += [role.name]
        prefixes_list += extra
        prefixes_list += [self.display_name]
        bot_info = {'display_name': self.display_name,
                    'description': self.description,
                    'guilds': [guild.name for guild in self.guilds],
                    'prefixes': prefixes_list,
                    'invite': 'https://discord.gg/m7e792Kg',
                    'help_command': self.help_invocation,
                    'owner': {key: value for key, value in self.creator._asdict().items() if key not in ['member_object', 'user_object']}}
        if os.path.isfile(pathmaker(APPDATA['debug'], 'general_debug')):
            bot_info = bot_info | loadjson(pathmaker(APPDATA['debug'], 'general_debug'))
        writejson(bot_info, pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/bot_info.json'))
        log.debug('bot doc info save to ' + pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/bot_info.json'))

    async def on_ready(self):
        log.info('%s has connected to Discord!', self.user.name)
        log.info('Bot is currently rate limited: %s', str(self.is_ws_ratelimited()))
        await self._get_bot_info()
        await self._start_sessions()
        await self.wait_until_ready()
        await self.set_delayed_bot_attributes()
        await asyncio.sleep(2)
        await self.support.to_all_subsupports(attribute_name='if_ready')
        await self.to_all_cogs('on_ready_setup')
        await self.create_doc_json()
        if self.is_debug is True:
            await self.debug_function()
        if BASE_CONFIG.getboolean('startup_message', 'use_startup_message') is True:
            await self.send_startup_message()
        await self.handle_previous_shutdown_msg()
        self._watch_for_shutdown_trigger.start()
        self._watch_for_config_changes.start()
        self._watch_for_alias_changes.start()
        log.info("Bot is ready")

    async def handle_previous_shutdown_msg(self):
        if os.path.isfile(self.shutdown_message_pickle_file):
            last_shutdown_message = get_pickled(self.shutdown_message_pickle_file)
            channel_id = last_shutdown_message.get('channel_id')
            message_id = last_shutdown_message.get('message_id')
            channel = await self.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
            os.remove(self.shutdown_message_pickle_file)

    async def set_delayed_bot_attributes(self):
        self.on_command_error = self.support.handle_errors

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_config_changes(self):
        # TODO: How to make sure they are also correctly restarted, regarding all loops on the bot
        async for changes in awatch(APPDATA['config'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
            BASE_CONFIG.read()
            COGS_CONFIG.read()
            await self.to_all_cogs('update', typus='data')

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_alias_changes(self):
        async for changes in awatch(APPDATA['command_aliases.json'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
            await self.to_all_cogs('update', typus='data')

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_shutdown_trigger(self):
        async for changes in awatch(APPDATA['shutdown_trigger'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
                if change_typus is Change.added:
                    name, extension = os.path.basename(change_path).split('.')
                    if extension.casefold() == 'trigger':
                        if name.casefold() == 'shutdown':
                            await self.close()
                        elif name.casefold() == 'emergency_shutdown':
                            sys.exit()

    async def on_message(self, message: discord.Message) -> None:
        if self.is_ready() is True:
            await self.support.record_channel_usage(message)
        await self.process_commands(message)

    async def send_startup_message(self):
        channel = await self.channel_from_name(BASE_CONFIG.get('startup_message', 'channel'))

        delete_time = 60 if self.is_debug is True else BASE_CONFIG.getint('startup_message', 'delete_after')
        delete_time = None if delete_time <= 0 else delete_time
        title = f"**{BASE_CONFIG.get('startup_message', 'title').title()}**"
        description = BASE_CONFIG.get('startup_message', 'description')
        image = BASE_CONFIG.get('startup_message', 'image')
        if BASE_CONFIG.getboolean('startup_message', 'as_embed') is True:
            embed_data = await self.make_generic_embed(author='bot_author', footer='feature_request_footer', image=image, title=title, description=description, thumbnail='no_thumbnail', type='image')
            self.used_startup_message = await channel.send(**embed_data, delete_after=delete_time)
        else:
            msg = f"{title}\n\n{description}\n\n{image}"
            self.used_startup_message = await channel.send(msg, delete_after=delete_time)

    async def to_all_cogs(self, command, *args, **kwargs):
        for cog_name, cog_object in self.cogs.items():
            if hasattr(cog_object, command):
                await getattr(cog_object, command)(*args, **kwargs)

    async def _get_bot_info(self):
        if self.all_bot_roles is None:
            self.all_bot_roles = []
            self.bot_member = await self.retrieve_antistasi_member(self.id)
            for index, role in enumerate(self.bot_member.roles):
                if index != 0:
                    self.all_bot_roles.append(role)
        self.command_prefix = BASE_CONFIG.get('prefix', 'command_prefix')
        if BASE_CONFIG.getboolean('prefix', 'invoke_by_role_and_mention') is True:
            self.command_prefix = when_mentioned_or_roles_or(BASE_CONFIG.get('prefix', 'command_prefix'))

        AntiPetrosBot.creator = self.creator._replace(**{'member_object': await self.retrieve_antistasi_member(self.creator.id), 'user_object': await self.fetch_user(self.creator.id)})
        os.environ['BOT_CREATOR_NAME'] = self.creator.name
        os.environ['BOT_CREATOR_ID'] = str(self.creator.id)

    async def _start_sessions(self):
        if self.aio_request_session is None:
            self.aio_request_session = aiohttp.ClientSession(loop=self.loop)
            self.clients_to_close.append(self.aio_request_session)
            log.debug("'%s' was started", str(self.aio_request_session))

    def _get_initial_cogs(self):
        """
        Loads `Cogs` that are enabled.

        If a Cog is enabled is determined, by:
            - `bot_admin_cogs` are always enabled
            - `discord_admin_cogs are also always enabled
            - `dev_cogs` are only enabled when running locally under `AntiDEVtros`
            - all other cogs are looked up in `base_config.ini` under the section `extensions` if they are set to enabled (checks bool value)

        New Cogs need to be added to `base_config.ini` section `extensions` in the format `[folder_name].[file_name without '.py']=[yes | no]`
            example: `general_cogs.klimbim_cog=yes`
        """
        for essential_cog_path in self.essential_cog_paths:
            self.load_extension(f"{self.cog_import_base_path}.{essential_cog_path}")
            log.debug("loaded Essential-Cog: '%s' from '%s'", essential_cog_path.split('.')[-1], f"{self.cog_import_base_path}.{essential_cog_path}")
        if self.is_debug is True:
            for dev_cog_path in self.dev_cog_paths:
                self.load_extension(f"{self.cog_import_base_path}.{dev_cog_path}")
                log.debug("loaded Development-Cog: '%s' from '%s'", dev_cog_path.split('.')[-1], f"{self.cog_import_base_path}.{dev_cog_path}")
        for _cog in BASE_CONFIG.options('extensions'):
            if BASE_CONFIG.getboolean('extensions', _cog) is True:
                name = _cog.split('.')[-1]
                full_import_path = self.cog_import_base_path + '.' + _cog
                self.load_extension(full_import_path)
                log.debug("loaded extension-cog: '%s' from '%s'", name, full_import_path)

        log.info("extensions-cogs loaded: %s", ', '.join(self.cogs))

    async def close(self):
        try:
            if self.used_startup_message is not None:
                await self.used_startup_message.delete()
        except discord.NotFound:
            log.debug('startup message was already deleted')
        log.info("shutting down bot loops")
        self.update_check_loop.stop()

        log.info("retiring troops")
        self.support.retire_subsupport()

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

    @ staticmethod
    def activity_from_config(option='standard_activity'):
        activity_dict = {'playing': discord.ActivityType.playing,
                         'watching': discord.ActivityType.watching,
                         'listening': discord.ActivityType.listening,
                         'streaming': discord.ActivityType.streaming}
        text, activity_type = BASE_CONFIG.getlist('activity', option)
        text = text.title()
        if activity_type not in activity_dict:
            log.critical("'%s' is not an Valid ActivityType, aborting activity change")
            return
        activity_type = activity_dict.get(activity_type)

        return discord.Activity(name=text, type=activity_type)

    @ tasks.loop(minutes=5, reconnect=True)
    async def update_check_loop(self):
        if self.current_day == datetime.utcnow().day:
            return
        self.current_day = datetime.utcnow().day
        await self.to_all_subsupports('update', typus='time')
        await self.to_all_cogs('updated', typus='time')

    @ update_check_loop.before_loop
    async def before_update_check_loop(self):
        await self.wait_until_ready()

    def all_cog_commands(self):
        for cog_name, cog_object in self.cogs.items():
            for command in cog_object.get_commands():
                yield command

    async def get_antistasi_emoji(self, name):
        for _emoji in self.antistasi_guild.emojis:
            if _emoji.name.casefold() == name.casefold():
                return _emoji

    async def not_implemented(self, ctx: commands.Context):
        embed_data = await self.make_generic_embed(title='NOT IMPLEMENTED',
                                                   description='Sorry but the command is a Placeholder and is not yet implemented',
                                                   author='bot_author',
                                                   footer='feature_request_footer',
                                                   thumbnail="under_construction")
        await ctx.send(**embed_data)

    @property
    def admins(self):
        role = {role.name.casefold(): role for role in self.antistasi_guild.roles}.get("admin".casefold())
        _out = []
        for member in self.antistasi_guild.members:
            if role in member.roles:
                _out.append(member)
        return list(set(_out))

    @ property
    def id(self):
        return self.user.id

    @ property
    def display_name(self):
        return self.bot.user.display_name

    @ property
    def is_debug(self):
        dev_env_var = os.getenv('IS_DEV', 'false')
        if dev_env_var.casefold() == 'true':
            return True
        elif dev_env_var.casefold() == 'false':
            return False
        else:
            raise RuntimeError('is_debug')

    @ property
    def blacklisted_users(self):
        return loadjson(APPDATA['blacklist.json'])

    @ property
    def notify_contact_member(self):
        return BASE_CONFIG.get('blacklist', 'notify_contact_member')

    @ property
    def std_date_time_format(self):
        return "%Y-%m-%d %H:%M:%S"

    @ property
    def shutdown_command(self):
        return self.get_command('shutdown')

    def blacklisted_user_ids(self):
        for user_item in self.blacklisted_users:
            yield user_item.get('id')

    async def message_creator(self, message=None, embed=None, file=None):
        if message is None and embed is None:
            message = 'message has no content'
        await self.creator.member_object.send(content=message, embed=embed, file=file)

    async def split_to_messages(self, ctx, message, split_on='\n', in_codeblock=False, syntax_highlighting='json'):
        _out = ''
        chunks = message.split(split_on)
        for chunk in chunks:
            if sum(map(len, _out)) + len(chunk + split_on) < self.max_message_length:
                _out += chunk + split_on
            else:
                if in_codeblock is True:
                    _out = f"```{syntax_highlighting}\n{_out}\n```"
                await ctx.send(_out)
                await asyncio.sleep(1)
                _out = ''
        if in_codeblock is True:
            _out = f"```{syntax_highlighting}\n{_out}\n```"
        await ctx.send(_out)

    def sync_channel_from_name(self, channel_name):
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

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
        role_data = []
        for role in self.antistasi_guild.roles:
            if role.name != '@everyone':
                role_members = [member.name for member in role.members]
                role_data.append({'name': role.name, 'position': role.position, 'tags': str(role.tags), 'members': role_members, 'managed': role.managed, 'hoist': role.hoist, 'created_at': role.created_at.strftime(self.std_date_time_format)})
        role_data = sorted(role_data, key=lambda x: x.get('position'))
        writejson(role_data, 'all_roles.json', sort_keys=False)
        log.debug("debug function finished")

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.__class__.__name__

    def __getattr__(self, attr_name):
        if hasattr(self.support, attr_name) is True:
            return getattr(self.support, attr_name)
        return getattr(super(), attr_name)

# endregion[SpecialMethods]
