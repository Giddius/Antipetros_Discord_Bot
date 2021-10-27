"""
Actual Bot class.

"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import time
import asyncio
import shutil
# * Third Party Imports --------------------------------------------------------------------------------->
import aiohttp
from inspect import getdoc
import discord
from typing import Callable, Any, Iterable, TYPE_CHECKING, Union, Optional, Generator, AsyncGenerator, List
from aiodav import Client as AioWebdavClient
from collections import UserDict, namedtuple
from watchgod import awatch
from discord.ext import tasks, commands, ipc
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from itertools import product
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.engine.global_checks import user_not_blacklisted
from antipetros_discordbot.auxiliary_classes.version_item import VersionItem
from antipetros_discordbot.engine.special_prefix import when_mentioned_or_roles_or
from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
from antipetros_discordbot.utility.gidtools_functions import get_pickled, pathmaker, readit, writeit, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.cogs import BOT_ADMIN_COG_PATHS, DISCORD_ADMIN_COG_PATHS, DEV_COG_PATHS
from datetime import datetime
from antipetros_discordbot.utility.emoji_handling import is_unicode_emoji
from antipetros_discordbot.engine.replacements import CommandCategory, AntiPetrosBaseContext, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosBaseCog, AntiPetrosFlagCommand
from antipetros_discordbot.schemas.bot_schema import AntiPetrosBotSchema
from antipetros_discordbot.utility.sqldata_storager import ChannelUsageResult
from antipetros_discordbot.auxiliary_classes.asking_items import AbstractUserAsking
from antipetros_discordbot.cogs.community_events_cogs.voting_cog import VoteItem
from discord.client import _cleanup_loop, _cancel_tasks
from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.utility.asyncio_helper import RestartBlocker, message_delete
import signal
import platform
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

    def __init__(self, bot: "AntiPetrosBot", case_folded: bool = True) -> None:
        super().__init__()
        self.bot = bot
        self.case_folded = case_folded
        self._collect_commands()

    def _collect_commands(self):
        self.data = {}
        for command in set(self.bot.all_commands.values()):
            names = [command.name] + command.aliases
            for name in names:
                self.data[name] = command
            if command.is_group is True:
                for sub_command in command.commands:
                    sub_names = [sub_command.name] + sub_command.aliases
                    for p_name, s_name in product(names, sub_names):
                        self.data[f"{p_name} {s_name}"] = sub_command
        if self.case_folded is True:
            self.data = {key.casefold(): value for key, value in self.data.items()}

    async def sort_commands(self, usage_counter):

        self.data = {key: value for key, value in sorted(self.data.items(), key=lambda x: usage_counter.get(x[1].name, 0), reverse=True)}

    def get(self, key, default=None):
        if self.case_folded is True:
            key = key.casefold()
        return self.data.get(key, default)

    async def update_commands(self):
        self._collect_commands()


class AntiPetrosBot(commands.Bot):

    # region [ClassAttributes]
    app_name = os.getenv('APP_NAME')
    author_name = os.getenv('AUTHOR_NAME')

    ToUpdateItem = namedtuple("ToUpdateItem", ["function", "typus_triggers"])
    creator_id = 576522029470056450
    launch_date = datetime(year=2021, month=3, day=11)

    discord_admin_cog_import_path = "antipetros_discordbot.cogs.discord_admin_cogs.discord_admin_cog"
    testing_channel = BASE_CONFIG.retrieve("debug", "current_testing_channel", typus=str, direct_fallback='bot-testing')
    essential_cog_paths = BOT_ADMIN_COG_PATHS + DISCORD_ADMIN_COG_PATHS
    dev_cog_paths = DEV_COG_PATHS

    description_file = pathmaker(APPDATA['documentation'], 'bot_description.md')
    brief_file = pathmaker(APPDATA['documentation'], 'bot_brief.md')
    long_description_file = pathmaker(APPDATA['documentation'], 'bot_long_description.md')
    extra_info_file = pathmaker(APPDATA['documentation'], 'bot_extra_info.md')
    short_doc_file = pathmaker(APPDATA['documentation'], 'bot_short_doc.md')

    activity_dict = {'playing': discord.ActivityType.playing,
                     'watching': discord.ActivityType.watching,
                     'listening': discord.ActivityType.listening,
                     'streaming': discord.ActivityType.streaming}

    max_message_length = 1900
    schema = AntiPetrosBotSchema()
    is_shutting_down_event = asyncio.Event()
    is_shutting_down_event.clear()
# endregion[ClassAttributes]

    def __init__(self, token: str = None, ** kwargs):

        # region [Init]
        self.setup_finished = False
        super().__init__(owner_ids=set([self.creator_id] + [_id for _id in BASE_CONFIG.retrieve('general_settings', 'owner_ids', typus=List[int], direct_fallback=[])]),
                         case_insensitive=BASE_CONFIG.getboolean('command_settings', 'invocation_case_insensitive'),
                         self_bot=False,
                         command_prefix=when_mentioned_or_roles_or(),
                         intents=self._get_intents(),
                         chunk_guilds_at_startup=True,
                         member_cache_flags=discord.MemberCacheFlags.all(),
                         help_command=None,
                         strip_after_prefix=True,
                         ** kwargs)

        self.to_update_methods: list[self.ToUpdateItem] = []
        self.token: str = token
        self.activity_update_task: asyncio.Task = None
        self.support: BotSupporter = None
        self.used_startup_message = None
        self._command_dict: dict = None
        self.connect_counter: int = 0
        self.special_prefixes = None
        self.prefix_role_exceptions = None
        self.use_invoke_by_role_and_mention = None
        self.set_prefix_params()
        self.to_update_methods.append(self.ToUpdateItem(self.update_prefix_params, [UpdateTypus.CONFIG, UpdateTypus.CYCLIC]))
        self.after_invoke(self.after_command_invocation)
        self.restart_blocker: RestartBlocker = RestartBlocker()
        self.updated_lock = asyncio.Lock()
        self._setup()

        glog.class_init_notification(log, self)

# endregion[Init]

# region [Setup]

    def _setup(self) -> None:
        CommandCategory.bot = self
        self.support = BotSupporter(self)
        self.support.recruit_subsupports()
        self.add_self_to_classes()
        self.add_check(user_not_blacklisted)
        self._get_initial_cogs()
        COGS_CONFIG.read()
        if os.getenv('INFO_RUN') == "1":
            self._info_run()

    async def on_resumed(self) -> None:
        log.critical("Bot was reconnected and has resumed the session!")
        self.connect_counter += 1
        await self._check_if_all_cogs_ready()
        await self.to_all_as_tasks('update', False, typus=UpdateTypus.RECONNECT)

    async def async_setup(self) -> None:
        await self.wait_until_ready()
        log.info('%s has connected to Discord!', self.name)
        self.setup_finished = False

        self.connect_counter += 1
        await self._ensure_guild_is_chunked()
        if self.connect_counter == 1:

            if platform.system() == 'Linux':
                self.loop.add_signal_handler(signal.SIGINT, self.shutdown_signal)
                self.loop.add_signal_handler(3, self.shutdown_signal)  # 3 -> SIGQUIT
            asyncio.create_task(self.send_startup_message())
            asyncio.create_task(self._start_watchers())
            await self.set_activity()
            await self._make_stored_dicts()
            await self.to_all_as_tasks('on_ready_setup', True)
            await self._check_if_all_cogs_ready()

        await self._make_command_dict()
        await self.process_meta_data()
        self.setup_finished = True
        log.info("Bot is ready")
        log.info('%s End of Setup Procedures %s', '+-+' * 15, '+-+' * 15)

        if os.getenv('CONFIG_FILL_RUN', '0') == '1':
            await asyncio.sleep(10)
            await self.close()


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

    def add_self_to_classes(self) -> None:
        ChannelUsageResult.bot = self
        AbstractUserAsking.bot = self

    async def _ensure_guild_is_chunked(self) -> None:
        if self.antistasi_guild.chunked is False:
            log.debug("Antistasi Guild is not chunked, chunking Guild now")
            await self.antistasi_guild.chunk(cache=True)
            log.debug("finished chunking Antistasi Guild")

    async def _start_watchers(self) -> None:
        while self.setup_finished is False:
            await asyncio.sleep(0.1)
        self._watch_for_config_changes.start()
        self._watch_for_alias_changes.start()

    def _info_run(self) -> None:

        target_folder = pathmaker(os.getenv('INFO_RUN_DUMP_FOLDER'))

        writejson(self.dump(), pathmaker(target_folder, 'bot_data.json'), default=str, sort_keys=False)
        print('Collected Bot-data')

        cog_data = [cog_object.dump() for cog_object in self.cogs.values() if cog_object.name.casefold() != "generaldebugcog"]
        writejson(cog_data, pathmaker(target_folder, 'cogs_data.json'), default=str, sort_keys=False)
        print('Collected Cogs-data')

        command_data = [command_object.dump() for command_object in self.commands if command_object.cog_name.casefold() != 'generaldebugcog']
        writejson(command_data, pathmaker(target_folder, 'commands_data.json'), default=str, sort_keys=False)
        print('Collected Commands-data')

        missing_docstring_data = {'cogs': [], 'commands': [], 'loops': [], 'listener': []}
        for cog_name, cog_object in self.cogs.items():
            if cog_object.name.casefold() != "generaldebugcog":
                if cog_object.docstring in {'', 'WiP', None}:
                    missing_docstring_data['cogs'].append(cog_name)

                for command in cog_object.get_commands():
                    if command.docstring in {'', 'WiP', None}:
                        missing_docstring_data['commands'].append(f"{cog_object.name}.{command.name}")

                for loop_name, loop_object in cog_object.loops.items():
                    if getdoc(loop_object.coro) in {'', 'WiP', None}:
                        missing_docstring_data['loops'].append(f"{cog_object.name}.{loop_name}")

                for listener in cog_object.all_listeners:
                    if listener.description in {'', 'WiP', None}:
                        missing_docstring_data['listener'].append(f"{cog_object.name}.{listener.name}")
        writejson(missing_docstring_data, pathmaker(target_folder, 'missing_docstring_data.json'), default=str, sort_keys=False)
        print('Collected Missing-Docstring-Data')

    async def _make_command_dict(self) -> None:
        self._command_dict = await asyncio.to_thread(CommandAutoDict, self, True)
        update_item = self.ToUpdateItem(self._command_dict.update_commands, [UpdateTypus.COMMANDS, UpdateTypus.ALIAS, UpdateTypus.CONFIG, UpdateTypus.CYCLIC])
        if update_item not in self.to_update_methods:
            self.to_update_methods.append(update_item)

    def set_prefix_params(self) -> None:
        self.special_prefixes = list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))
        self.prefix_role_exceptions = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_exceptions', typus=List[str], direct_fallback=[])
        self.use_invoke_by_role_and_mention = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_and_mention', typus=bool, direct_fallback=True)

    async def update_prefix_params(self) -> None:
        self.special_prefixes = list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))
        self.prefix_role_exceptions = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_exceptions', typus=List[str], direct_fallback=[])
        self.use_invoke_by_role_and_mention = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_and_mention', typus=bool, direct_fallback=True)
        log.debug("prefix_params were updated")

# endregion[Setup]

# region [Properties]

    @ property
    def id(self) -> int:
        return self.user.id

    @property
    def name(self) -> str:
        return self.user.name

    @ property
    def display_name(self) -> str:
        return self.bot.user.display_name

    @property
    def description(self) -> str:
        if os.path.isfile(self.description_file) is False:
            writeit(self.description_file, '')
        return readit(self.description_file)

    @property
    def brief(self) -> str:
        if os.path.isfile(self.brief_file) is False:
            writeit(self.brief_file, '')
        return readit(self.brief_file)

    @property
    def long_description(self) -> str:
        if os.path.isfile(self.long_description_file) is False:
            writeit(self.long_description_file, '')
        return readit(self.long_description_file)

    @property
    def short_doc(self) -> str:
        if os.path.isfile(self.short_doc_file) is False:
            writeit(self.short_doc_file, '')
        return readit(self.short_doc_file)

    @property
    def extra_info(self) -> str:
        if os.path.isfile(self.extra_info_file) is False:
            writeit(self.extra_info_file, '')
        return readit(self.extra_info_file)

    @description.setter
    def description(self, value) -> None:
        if self.description.casefold() in ['wip', None, '']:
            writeit(self.description_file, value)

    @property
    def creator(self) -> discord.Member:
        return self.get_antistasi_member(self.creator_id)

    @property
    def member(self) -> discord.Member:
        return self.get_antistasi_member(self.id)

    @property
    def roles(self) -> list[discord.Role]:
        return [role for role in self.member.roles if role is not self.everyone_role]

    @property
    def github_url(self) -> str:
        return BASE_CONFIG.retrieve('links', 'bot_github_repo', typus=str, direct_fallback="https://github.com/404")

    @property
    def github_wiki_url(self) -> str:
        return BASE_CONFIG.retrieve('links', 'bot_github_wiki', typus=str, direct_fallback="https://github.com/404")

    @property
    def portrait_url(self) -> str:
        option_name = f"{self.display_name.casefold()}_portrait_image"
        return BASE_CONFIG.retrieve('links', option_name, typus=str, direct_fallback=None)

    @ property
    def is_debug(self) -> bool:
        dev_env_var = os.getenv('IS_DEV', 'false')
        if dev_env_var.casefold() == 'true':
            return True
        elif dev_env_var.casefold() == 'false':
            return False
        else:
            raise RuntimeError('is_debug')

    @ property
    def notify_contact_member(self) -> str:
        return BASE_CONFIG.get('blacklist', 'notify_contact_member')

    @property
    def commands_map(self) -> dict[str, Union[AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand]]:
        if self._command_dict is None:
            self._make_command_dict()
        return self._command_dict

    @property
    def non_mention_prefixes(self) -> list[str]:
        return list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))

    @property
    def all_prefixes(self) -> list[str]:
        prefixes = list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))
        for role in self.member.roles:
            if role.name.casefold() not in ['dev helper', 'antidevtros'] and role.id != 860679762661867600 and role.id != 839778664702148608:
                prefixes.append(role.mention)
        prefixes.append(self.member.mention)
        sorted_prefixes = sorted(list(set(prefixes)), key=lambda x: (str(self.id) in x, x.startswith('<'), is_unicode_emoji(x)), reverse=True)

        return sorted_prefixes

    @property
    def all_prefixes_for_check(self) -> list[str]:
        prefixes = list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))
        for role in self.member.roles:
            if role.name.casefold() not in ['dev helper'] and role is not self.everyone_role:
                prefixes.append(role.mention)
                prefixes.append(role.mention.replace('<@', '<@!'))
        prefixes.append(self.member.mention)
        prefixes.append(self.member.mention.replace('<@', '<@!'))
        sorted_prefixes = sorted(list(set(prefixes)), key=lambda x: (str(self.id) in x, x.startswith('<'), is_unicode_emoji(x)), reverse=True)

        return sorted_prefixes

    @property
    def version(self) -> VersionItem:
        version_string = os.getenv('ANTIPETROS_VERSION')
        return VersionItem.from_string(version_string)

    @property
    def cog_list(self) -> list[AntiPetrosBaseCog]:
        return list(self.cogs.values())


# endregion[Properties]

# region [Loops]


    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_config_changes(self) -> None:
        # TODO: How to make sure they are also correctly restarted, regarding all loops on the bot
        if self.setup_finished is False:
            return
        async for changes in awatch(APPDATA['config'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))
                await asyncio.to_thread(COGS_CONFIG.read)
                await asyncio.to_thread(BASE_CONFIG.read)
            await self.to_all_as_tasks('update', wait=False, typus=UpdateTypus.CONFIG)

    @ tasks.loop(count=1, reconnect=True)
    async def _watch_for_alias_changes(self) -> None:
        if self.setup_finished is False:
            return
        async for changes in awatch(APPDATA['command_aliases.json'], loop=self.loop):
            for change_typus, change_path in changes:
                log.debug("%s ----> %s", str(change_typus).split('.')[-1].upper(), os.path.basename(change_path))

            await self.to_all_as_tasks('update', wait=True, typus=UpdateTypus.ALIAS)


# endregion[Loops]

# region [Helper]


    @staticmethod
    def _get_intents() -> discord.Intents:
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

    async def _try_delete_startup_message(self) -> None:
        if self.used_startup_message is not None:
            try:
                await self.used_startup_message.delete()
                log.debug('deleted startup message')
            except discord.NotFound:
                log.debug('startup message was already deleted')

    async def after_command_invocation(self, ctx: AntiPetrosBaseContext) -> None:
        method_name = "execute_on_after_command_invocation"
        await self.to_all_as_tasks(method_name, False, ctx)

    async def on_command_error(self, ctx: commands.Context, exception: Exception) -> None:
        method_name = "execute_on_command_errors"
        await self.to_all_as_tasks(method_name, False, ctx, exception)
# endregion[Helper]

    async def send_startup_message(self) -> None:
        while self.setup_finished is False:
            await asyncio.sleep(1)
        await asyncio.sleep(2)

        await self._handle_previous_shutdown_msg()
        if BASE_CONFIG.getboolean('startup_message', 'use_startup_message') is False:
            return
        if self.is_debug is True:
            channel = self.channel_from_name(self.testing_channel)
            embed_data = await self.make_generic_embed(title=f"{self.display_name} is Ready",
                                                       fields=[self.bot.field_item(name='Is Debug Session', value=str(self.is_debug))])
            await channel.send(**embed_data, delete_after=60)
            return
        guild = self.get_guild(self.get_antistasi_guild_id())
        channel = discord.utils.get(guild.channels, name=BASE_CONFIG.retrieve('startup_message', 'channel', typus=str, direct_fallback='bot-testing'))

        delete_time = 60 if self.is_debug is True else BASE_CONFIG.getint('startup_message', 'delete_after')
        delete_time = None if delete_time <= 0 else delete_time
        title = f"**{BASE_CONFIG.get('startup_message', 'title').title()}**"
        description = BASE_CONFIG.get('startup_message', 'description')
        image = BASE_CONFIG.get('startup_message', 'image')

        log.info("sending startup message")
        if BASE_CONFIG.getboolean('startup_message', 'as_embed') is True:
            embed_data = await self.make_generic_embed(author='bot_author', footer='feature_request_footer', image=image, title=title, description=description, thumbnail='no_thumbnail', type='image')
            self.used_startup_message = await channel.send(**embed_data, delete_after=delete_time)
        else:
            msg = f"{title}\n\n{description}\n\n{image}"
            self.used_startup_message = await channel.send(msg)
            await message_delete(self.used_startup_message, delete_time, self.is_shutting_down_event)

    async def _handle_previous_shutdown_msg(self) -> None:
        log.debug("shutdown_message_pickle_file = %s, exists=%s", self.shutdown_message_pickle_file, str(os.path.isfile(self.shutdown_message_pickle_file)))
        if os.path.isfile(self.shutdown_message_pickle_file):
            log.info("trying to remove old shutdown message")
            try:
                last_shutdown_message = get_pickled(self.shutdown_message_pickle_file)
                message = await self.get_message_directly(last_shutdown_message.get('channel_id'), last_shutdown_message.get('message_id'))
                await message.delete()
            except Exception as error:
                log.debug(error)
            finally:
                os.remove(self.shutdown_message_pickle_file)

    async def to_all_as_tasks(self, command: str, wait: bool, *args, **kwargs) -> None:
        all_tasks = []
        all_target_objects = [cog_object for cog_object in self.cogs.values()] + [subsupport for subsupport in self.subsupports]
        for target_object in all_target_objects:
            if hasattr(target_object, command):
                all_tasks.append(asyncio.create_task(getattr(target_object, command)(*args, **kwargs)))

        if all_tasks and wait is True:
            await asyncio.gather(*all_tasks)

    async def to_all_cogs(self, command: str, *args, **kwargs) -> None:
        all_tasks = []
        for cog_name, cog_object in self.cogs.items():
            if hasattr(cog_object, command):
                all_tasks.append(asyncio.create_task(getattr(cog_object, command)(*args, **kwargs), name=f"{cog_name}_{command}"))

        if all_tasks:
            await asyncio.gather(*all_tasks)
            log.info("All '%s' methods finished", command)

    async def _check_if_all_cogs_ready(self) -> None:
        for cog_name, cog_object in self.cogs.items():
            if cog_object.ready is False:
                raise RuntimeError(f"cog {cog_name} never finished on_ready_setup")

    def _get_initial_cogs(self) -> None:
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

    async def set_activity(self) -> None:
        # TODO: make dynamic
        actvity_type = self.activity_dict.get('watching')
        value = len([member.id for member in self.bot.antistasi_guild.members if member.status is discord.Status.online])
        text = f"{value} User currently in this Guild"
        await self.change_presence(activity=discord.Activity(type=actvity_type, name=text))
        # if self.ToUpdateItem(self.set_activity, [UpdateTypus.CYCLIC, UpdateTypus.MEMBERS]) not in self.to_update_methods:
        #     self.to_update_methods.append(self.ToUpdateItem(self.set_activity, [UpdateTypus.CYCLIC, UpdateTypus.MEMBERS]))

        self.activity_update_task = asyncio.create_task(self.update_activity())

    async def update_activity(self) -> None:
        await asyncio.sleep(300)
        await self.set_activity()

    def get_cog(self, name: str) -> Union[commands.Cog, AntiPetrosBaseCog]:
        return {cog_name.casefold(): cog for cog_name, cog in self.cogs.items()}.get(name.casefold())

    def all_cog_commands(self) -> AsyncGenerator[Union[commands.Command, AntiPetrosBaseCommand, AntiPetrosBaseGroup], None]:
        for cog_name, cog_object in self.cogs.items():
            for command in cog_object.get_commands():
                yield command

    def add_update_method(self, meth: Callable, *typus: UpdateTypus) -> None:
        self.to_update_methods.append(self.ToUpdateItem(meth, list(typus)))

    def dump(self) -> dict:
        return self.schema.dump(self)
# region [SpecialMethods]

    async def get_context(self, message: discord.Message, *, cls: commands.Context = None) -> Union[AntiPetrosBaseContext, commands.Context]:
        cls = AntiPetrosBaseContext if cls is None else cls
        return await super().get_context(message, cls=cls)

    def _clean_temp_folder(self) -> None:
        for item in os.scandir(APPDATA["temp_files"]):
            if item.is_file():
                os.remove(item.path)

            elif item.is_dir():
                shutil.rmtree(item.path)

    async def close(self) -> None:
        self.is_shutting_down_event.set()
        log.info("waiting on cleanup message tasks.")

        for task in asyncio.all_tasks():
            if any(task.get_name().startswith(prefix) for prefix in {'TEMP_EMOJI_REMOVAL', 'TEMP_MESSAGE_REMOVAL', "INVOCATION_MESSAGE_REMOVAL", "DELETE_AFTER_MESSAGE_REMOVAL", "STORED_MESSAGE_REMOVAL"}):
                if task.done():
                    continue
                await task
                log.info("cleanup message task done: %r", task.get_name())
        self._watch_for_alias_changes.cancel()

        self._watch_for_config_changes.cancel()

        log.info("retiring troops")
        await self.support.retire_subsupport()

        if self.activity_update_task is not None:
            self.activity_update_task.cancel()

        await asyncio.sleep(5)
        try:
            await general_db.shutdown()
        except Exception as error:
            log.error(error, exc_info=True)
        log.info("calling bot method super().close()")

        await super().close()
        self._clean_temp_folder()
        time.sleep(2)

    async def start(self, *args, **kwargs) -> None:
        asyncio.create_task(self.async_setup())
        await super().start(self.token, reconnect=True, bot=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        return self.__class__.__name__

    def __getattr__(self, attr_name: str) -> Any:
        if hasattr(self.support, attr_name) is True:
            return getattr(self.support, attr_name)
        return getattr(super(), attr_name)

# endregion[SpecialMethods]


if __name__ == '__main__':
    x = AntiPetrosBot()
