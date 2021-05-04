"""
Actual Bot class.

"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
import time
import asyncio

# * Third Party Imports --------------------------------------------------------------------------------->
import aiohttp
import discord
from typing import List, Union, Mapping, Optional, Union, Hashable, Any

from collections import UserDict
from watchgod import Change, awatch
from discord.ext import tasks, commands, ipc
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.misc import save_bin_file
from antipetros_discordbot.engine.global_checks import user_not_blacklisted
from antipetros_discordbot.utility.named_tuples import CreatorMember
from antipetros_discordbot.engine.special_prefix import when_mentioned_or_roles_or
from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
from antipetros_discordbot.utility.gidtools_functions import get_pickled, loadjson, pathmaker, readit, writejson, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.cogs import BOT_ADMIN_COG_PATHS, DISCORD_ADMIN_COG_PATHS, DEV_COG_PATHS
from antipetros_discordbot.utility.converters import CommandConverter
from antipetros_discordbot.utility.data_gathering import save_cog_command_data


from antipetros_discordbot.engine.replacements import CommandCategory, AntiPetrosBaseGroup
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
import signal
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


class CommandAutoDict(UserDict):

    def __init__(self, bot: "AntiPetrosBot") -> None:
        super().__init__()
        self.bot = bot
        self._collect_commands()

    def _collect_commands(self):
        pass


class AntiPetrosBot(commands.Bot):

    # region [ClassAttributes]

    creator_id = 576522029470056450

    discord_admin_cog_import_path = "antipetros_discordbot.cogs.discord_admin_cogs.discord_admin_cog"
    testing_channel = BASE_CONFIG.retrieve("debug", "current_testing_channel", typus=str, direct_fallback='bot-testing')
    essential_cog_paths = BOT_ADMIN_COG_PATHS + DISCORD_ADMIN_COG_PATHS
    dev_cog_paths = DEV_COG_PATHS
    description_file = pathmaker(APPDATA['documentation'], 'bot_description.md')
    activity_dict = {'playing': discord.ActivityType.playing,
                     'watching': discord.ActivityType.watching,
                     'listening': discord.ActivityType.listening,
                     'streaming': discord.ActivityType.streaming}

    max_message_length = 1900
# endregion[ClassAttributes]

    def __init__(self, token: str = None, ipc_key: str = None, ** kwargs):

        # region [Init]
        self.setup_finished = False
        super().__init__(owner_ids=set([self.creator_id] + [_id for _id in BASE_CONFIG.retrieve('general_settings', 'owner_ids', typus=List[int], direct_fallback=[])]),
                         case_insensitive=BASE_CONFIG.getboolean('command_settings', 'invocation_case_insensitive'),
                         self_bot=False,
                         command_prefix=when_mentioned_or_roles_or(),
                         intents=self.get_intents(),
                         fetch_offline_members=True,
                         member_cache_flags=discord.MemberCacheFlags.all(),
                         help_command=None,
                         strip_after_prefix=True,
                         ** kwargs)

        self.sessions = {}
        self.to_update_methods = []
        self.token = token
        self.ipc_key = ipc_key
        self.support = None
        self.used_startup_message = None
        self.ipc = None

        self._setup()

        glog.class_init_notification(log, self)

# endregion[Init]

# region [Setup]
    @universal_log_profiler
    def _setup(self):
        self._update_profiling_check()
        CommandCategory.bot = self
        self.support = BotSupporter(self)
        self.support.recruit_subsupports()
        self.overwrite_methods()
        self._handle_ipc()
        self.add_check(user_not_blacklisted)
        self._get_initial_cogs()

    @universal_log_profiler
    async def on_ready(self):
        signal.signal(signal.SIGINT, self.shutdown_signal)
        signal.signal(signal.SIGTERM, self.shutdown_signal)
        log.info('%s has connected to Discord!', self.name)

        await self._ensure_guild_is_chunked()
        await self._start_sessions()

        await self.support.to_all_subsupports(attribute_name='if_ready')
        await self.to_all_cogs('on_ready_setup')

        await self.send_startup_message()

        await self._start_watchers()

        await self.set_activity()
        self.setup_finished = True
        if os.getenv('INFO_RUN') == "1":
            await self._info_run()
        log.info("Bot is ready")
        log.info('%s End of Setup Procedures %s', '+-+' * 15, '+-+' * 15)

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        log.info(f"{self.ipc.host} {self.ipc.port} is ready")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

    async def _start_sessions(self):
        self.sessions = {}
        self.sessions['aio_request_session'] = aiohttp.ClientSession(loop=self.loop)
        log.info("Session '%s' was started", repr(self.sessions['aio_request_session']))

    @universal_log_profiler
    async def _ensure_guild_is_chunked(self):
        if self.antistasi_guild.chunked is False:
            log.debug("Antistasi Guild is not chunked, chunking Guild now")
            await self.antistasi_guild.chunk(cache=True)
            log.debug("finished chunking Antistasi Guild")

    async def _start_watchers(self):
        self._watch_for_shutdown_trigger.start()
        self._watch_for_config_changes.start()
        self._watch_for_alias_changes.start()

    async def _info_run(self):
        await asyncio.sleep(5)
        for cog_name, cog_object in self.cogs.items():
            print(f"Collecting command-info for '{cog_name}'")
            # TODO: Change to Schema dump
            save_cog_command_data(cog_object, output_file=os.getenv('INFO_RUN_OUTPUT_FILE'))
        await self.bot.close()

    def _handle_ipc(self):
        if BASE_CONFIG.retrieve('ipc', "use_ipc_server", typus=bool, direct_fallback=False) is True:
            if self.ipc_key is None:
                raise AttributeError("ipc_key is missing")
            self.ipc = ipc.Server(self, secret_key=self.ipc_key, host=BASE_CONFIG.retrieve('ipc', 'host', typus=str), port=BASE_CONFIG.retrieve('ipc', 'port', typus=int))

    def overwrite_methods(self):
        for name, meth in self.support.overwritten_methods.items():
            setattr(self, name, meth)

# endregion[Setup]

# region [Properties]

    @ property
    def id(self):
        return self.user.id

    @property
    def name(self):
        return self.user.name

    @ property
    def display_name(self):
        return self.bot.user.display_name

    @property
    def description(self):
        if os.path.isfile(self.description_file) is False:
            writeit(self.description_file, '')
        return readit(self.description_file)

    @description.setter
    def description(self, value):
        if self.description.casefold() in ['wip', None, '']:
            writeit(self.description_file, value)

    @property
    def creator(self):
        creator_member = self.antistasi_guild.get_member(self.creator_id)
        return CreatorMember(creator_member.name, self.creator_id, creator_member)

    @property
    def member(self):
        return self.antistasi_guild.get_member(self.id)

    @property
    def github_url(self):
        return BASE_CONFIG.retrieve('links', 'github_repo', typus=str, direct_fallback="https://github.com/404")

    @property
    def github_wiki_url(self):
        return BASE_CONFIG.retrieve('links', 'github_wiki', typus=str, direct_fallback="https://github.com/404")

    @property
    def portrait_url(self):
        option_name = f"{self.display_name.casefold()}_portrait_image"
        return BASE_CONFIG.retrieve('links', option_name, typus=str, direct_fallback=None)

    @ property
    def is_debug(self):
        dev_env_var = os.getenv('IS_DEV', 'false')
        if dev_env_var.casefold() == 'true':
            return True
        elif dev_env_var.casefold() == 'false':
            return False
        else:
            raise RuntimeError('is_debug')

    @universal_log_profiler
    @ property
    def notify_contact_member(self):
        return BASE_CONFIG.get('blacklist', 'notify_contact_member')

# endregion[Properties]

# region [Loops]

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_config_changes(self):
        # TODO: How to make sure they are also correctly restarted, regarding all loops on the bot
        async for changes in awatch(APPDATA['config'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
            self._update_profiling_check()
            await self.to_all_cogs('update', typus=UpdateTypus.CONFIG)

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_alias_changes(self):
        async for changes in awatch(APPDATA['command_aliases.json'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
            await self.to_all_cogs('update', typus=UpdateTypus.ALIAS)

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_shutdown_trigger(self):
        async for changes in awatch(APPDATA['shutdown_trigger'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
                if change_typus is Change.added:
                    name, extension = os.path.basename(change_path).split('.')
                    if extension.casefold() == 'trigger':
                        if name.casefold() == 'shutdown':
                            await self.shutdown_mechanic()
                        elif name.casefold() == 'emergency_shutdown':
                            sys.exit()


# endregion[Loops]

# region [Helper]


    @staticmethod
    def _update_profiling_check():
        profiling_enabled = BASE_CONFIG.retrieve('profiling', 'enable_profiling', typus=str, direct_fallback='0')
        os.environ['ANTIPETROS_PROFILING'] = profiling_enabled
        log.info("Profiling is %s", "ENABLED" if profiling_enabled == "1" else "DISABLED")

    @staticmethod
    def get_intents():

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


# endregion[Helper]

    async def send_startup_message(self):
        await self._handle_previous_shutdown_msg()
        if BASE_CONFIG.getboolean('startup_message', 'use_startup_message') is False:
            return
        if self.is_debug is True:
            channel = await self.channel_from_name(self.testing_channel)
            embed_data = await self.make_generic_embed(title=f"{self.display_name} is Ready",
                                                       fields=[self.bot.field_item(name='Is Debug Session', value=str(self.is_debug))])
            await channel.send(**embed_data, delete_after=60)
            return
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

    async def _handle_previous_shutdown_msg(self):
        if self.is_debug is False and os.path.isfile(self.shutdown_message_pickle_file):
            try:
                last_shutdown_message = get_pickled(self.shutdown_message_pickle_file)
                message = await self.get_message_directly(last_shutdown_message.get('channel_id'), last_shutdown_message.get('message_id'))
                await message.delete()
            except Exception as error:
                log.debug(error)
            finally:
                os.remove(self.shutdown_message_pickle_file)

    async def to_all_as_tasks(self, command, *args, **kwargs):
        all_tasks = []
        all_target_objects = [cog_object for cog_object in self.cogs.values()] + [subsupport for subsupport in self.subsupports]
        for target_object in all_target_objects:
            if hasattr(target_object, command):
                task = asyncio.create_task(getattr(target_object, command)(*args, **kwargs))
                all_tasks.append(task)
        return all_tasks

    async def to_all_cogs(self, command, *args, **kwargs):
        all_tasks = []
        for cog_name, cog_object in self.cogs.items():
            if hasattr(cog_object, command):
                task = asyncio.create_task(getattr(cog_object, command)(*args, **kwargs))
                all_tasks.append(task)
        if all_tasks:
            await asyncio.wait(all_tasks, return_when="ALL_COMPLETED", timeout=None)
            log.info("All 'on_ready_setup' methods finished")

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

    async def set_activity(self):
        actvity_type = self.activity_dict.get('watching')
        value = len([member.id for member in self.bot.antistasi_guild.members if member.status is discord.Status.online])
        text = f"{value} User currently in this Guild"
        await self.change_presence(activity=discord.Activity(type=actvity_type, name=text))
        if (self.set_activity, (UpdateTypus.MEMBERS, UpdateTypus.CYCLIC)) not in self.to_update_methods:
            self.to_update_methods.append((self.set_activity, (UpdateTypus.MEMBERS, UpdateTypus.CYCLIC)))

    def get_cog(self, name: str):
        return {cog_name.casefold(): cog for cog_name, cog in self.__cogs.items()}.get(name.casefold())

    async def command_by_name(self, query_command_name: str):
        command_name_dict = {}
        for command in self.commands:
            if isinstance(command, AntiPetrosBaseGroup):
                for subcommand in command.commands:
                    command_name_dict[f"{command.name}.{subcommand.name}".casefold()] = subcommand
                    command_name_dict[f"{command.name} {subcommand.name}".casefold()] = subcommand
                    for p_alias in command.aliases:
                        command_name_dict[f"{p_alias}.{subcommand.name}".casefold()] = subcommand
                        command_name_dict[f"{p_alias} {subcommand.name}".casefold()] = subcommand
                        for alias in subcommand.aliases:
                            command_name_dict[f"{command.name}.{alias}".casefold()] = subcommand
                            command_name_dict[f"{command.name} {alias}".casefold()] = subcommand
                            command_name_dict[f"{p_alias}.{alias}".casefold()] = subcommand
                            command_name_dict[f"{p_alias} {alias}".casefold()] = subcommand

            command_name_dict[command.name.casefold()] = command
            for alias in command.aliases:
                command_name_dict[alias.casefold()] = command

        writejson(list(command_name_dict.keys()), 'checky.json')
        return command_name_dict.get(query_command_name.casefold(), None)

    def all_cog_commands(self):
        for cog_name, cog_object in self.cogs.items():
            for command in cog_object.get_commands():
                yield command

    async def get_antistasi_emoji(self, name):
        for _emoji in self.antistasi_guild.emojis:
            if _emoji.name.casefold() == name.casefold():
                return _emoji

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

    async def reload_cog_from_command_name(self, command: Union[str, commands.Command]):
        if isinstance(command, str):
            converter = CommandConverter()
            command = await converter.no_context_convert(self, command)

        self.reload_extension(command.module.__name__)
        # file_name = f"{cog.config_name}_cog"
        # for option in BASE_CONFIG.options('extensions'):
        #     if option.split('.')[-1].casefold() == file_name.casefold():
        #         import_path = self.cog_import_base_path + '.' + option
        #         self.unload_extension(import_path)
        #         self.load_extension(import_path)
        #         for _cog_name, cog_object in self.cogs.items():
        #             if _cog_name.casefold() == cog_name.casefold():
        #                 await cog_object.on_ready_setup()
        #                 break
        #         break


# region [SpecialMethods]


    async def _try_delete_startup_message(self):
        if self.used_startup_message is not None:
            try:
                await self.used_startup_message.delete()
                log.debug('deleted startup message')
            except discord.NotFound:
                log.debug('startup message was already deleted')

    async def _close_sessions(self):
        for session_name, session in self.sessions.items():
            await session.close()
            log.info("'%s' was shut down", session_name)

    async def close(self):
        try:
            log.info("retiring troops")
            self.support.retire_subsupport()
            await self._close_sessions()

            await self.wait_until_ready()
        except Exception as error:
            log.error(error, exc_info=True)
        finally:
            log.info("closing bot")
            await super().close()

    def run(self, **kwargs):
        if self.token is None:
            raise RuntimeError("Discord Token is None")
        super().run(self.token, bot=True, reconnect=True, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.__class__.__name__

    def __getattr__(self, attr_name):
        if attr_name in self.sessions:
            return self.sessions[attr_name]
        if hasattr(self.support, attr_name) is True:
            return getattr(self.support, attr_name)
        return getattr(super(), attr_name)

# endregion[SpecialMethods]


if __name__ == '__main__':
    x = AntiPetrosBot()
