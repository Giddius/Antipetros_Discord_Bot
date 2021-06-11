"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
from typing import TYPE_CHECKING, Union
from inspect import getdoc, getsourcefile, getsourcelines
import discord
import inspect
from discord.ext import commands, tasks
import gidlogger as glog
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.checks import allowed_requester
from antipetros_discordbot.utility.misc import make_config_name, sync_antipetros_repo_rel_path, loop_starter
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.schemas import AntiPetrosBaseCogSchema
from antipetros_discordbot.auxiliary_classes.listener_object import ListenerObject
from antipetros_discordbot.utility.event_data import ListenerEvents
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit, writejson
from antipetros_discordbot.engine.replacements.helper import JsonMetaDataProvider
from enum import Enum, unique, auto
from antipetros_discordbot.utility.data import COMMAND_CONFIG_SUFFIXES
from antipetros_discordbot.utility.checks import AllowedChannelAndAllowedRoleCheck
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

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
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class RequiredFile:
    @unique
    class FileType(Enum):
        TEXT = auto()
        JSON = auto()

        def create(self, path, content):
            if self is self.TEXT:
                writeit(path, content)
            elif self is self.JSON:
                writejson(content, path)

        def __str__(self):
            return str(self.name)

    file_type_map = {'txt': FileType.TEXT,
                     'log': FileType.TEXT,
                     'md': FileType.TEXT,
                     'html': FileType.TEXT,
                     'env': FileType.TEXT,
                     'jinja': FileType.TEXT,
                     'json': FileType.JSON}

    def __init__(self, path, default_content, typus: Union[str, FileType] = None):
        self.path = pathmaker(path)
        self.name = os.path.basename(self.path)
        self.dir_path = os.path.dirname(self.path)
        self.default_content = default_content
        self.file_type = self.get_file_type(typus) if typus is None or isinstance(typus, str) else typus

    def get_file_type(self, in_typus) -> FileType:
        extension = self.name.split('.')[-1] if in_typus is None else in_typus.casefold()
        file_type = self.file_type_map.get(extension.casefold(), None)
        if file_type is None:
            raise TypeError(f"Required File '{self.path}' either has no extension or it is a directory and not a file")
        return file_type

    def ensure(self):
        if os.path.isdir(self.dir_path) is False:
            os.makedirs(self.dir_path)
        if os.path.isfile(self.path) is False:
            self.file_type.create(self.path, self.default_content)


class RequiredFolder:
    def __init__(self, path):
        self.path = pathmaker(path)
        self.name = os.path.basename(self.path)
        if '.' in self.name[1:]:
            raise TypeError(f"Required Folder '{self.path}' seems to be a file and not a directory")

    def ensure(self):
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)


class AntiPetrosBaseCog(commands.Cog):
    """
    AntiPetros variant of discord.py Cog.
    Has extra documentation attributes as Class-Attributes.

    Adds dynamic allowed-getters automatically to instances.
    Adds a `name` attribute.
    Adds `__repr__` and `__str__`.
    """
    meta_data_provider = JsonMetaDataProvider(pathmaker(APPDATA['documentation'], 'cog_meta_data.json'))
    public = True
    meta_status = CogMetaStatus.EMPTY

    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []
    color = 'default'
    schema = AntiPetrosBaseCogSchema()

    def __init__(self, bot: "AntiPetrosBot") -> None:
        self.ready = False
        self.name = self.__class__.__name__
        self.config_name = make_config_name(self.name)
        self.bot = bot
        self.support = self.bot.support
        self._ensure_files_and_folder()
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.meta_data_getter = self.meta_data_provider.get_auto_provider(self)
        self.meta_data_setter = self.meta_data_provider.set_auto_provider(self)
        self.loops = self.get_loops()
        self.meta_data_setter('docstring', self.docstring)
        self._ensure_config_data()

    def _ensure_config_data(self):

        if COGS_CONFIG.has_section(self.config_name) is False:
            COGS_CONFIG.add_section(self.config_name)
            log.info("Added section '%s' to cogs_config.ini", self.config_name)
        for command in self.get_commands():
            if any(isinstance(check, AllowedChannelAndAllowedRoleCheck) for check in command.checks):
                for suffix, default_value in COMMAND_CONFIG_SUFFIXES.values():
                    if COGS_CONFIG.has_option(self.config_name, f"{command.name.strip()}{suffix}") is False:
                        COGS_CONFIG.set(self.config_name, f"{command.name.strip()}{suffix}", str(default_value))
        for option, value in self.required_config_data.get("cogs_config").items():
            if COGS_CONFIG.has_option(self.config_name, option) is False:
                COGS_CONFIG.set(self.config_name, option, str(value))

    @property
    def description(self):
        _out = self.meta_data_getter('description')
        if not _out:
            _out = self.docstring
        return _out

    def get_loops(self):
        return {name: loop_object for name, loop_object in inspect.getmembers(self) if isinstance(loop_object, tasks.Loop)}

    @property
    def long_description(self):
        return self.meta_data_getter('long_description')

    @property
    def short_doc(self):
        return self.meta_data_getter('short_doc')

    @property
    def brief(self):
        return self.meta_data_getter('brief')

    @property
    def extra_info(self):
        return self.meta_data_getter('extra_info')

    @property
    def docstring(self):
        return getdoc(self.__class__)

    @property
    def all_listeners(self):
        return [ListenerObject(event=ListenerEvents(event_name), method=listener_method, cog=self) for event_name, listener_method in self.get_listeners()]

    @ property
    def all_commands(self) -> list:
        return self.get_commands()

    @property
    def github_link(self):
        repo_base_url = os.getenv('REPO_BASE_URL')
        rel_path = sync_antipetros_repo_rel_path(getsourcefile(self.__class__))
        source_lines = getsourcelines(self.__class__)
        start_line_number = source_lines[1]
        code_length = len(source_lines[0])
        code_line_numbers = tuple(range(start_line_number, start_line_number + code_length))
        full_path = '/'.join([repo_base_url, rel_path, f'#L{min(code_line_numbers)}-L{max(code_line_numbers)}'])
        return full_path

    @property
    def github_wiki_link(self):
        wiki_base_url = os.getenv('WIKI_BASE_URL')
        full_path = '/'.join([wiki_base_url, self.name])
        return full_path

    def _ensure_files_and_folder(self):
        for item in self.required_folder + self.required_files:
            item.ensure()

    async def on_ready_setup(self):
        for loop_name, loop in self.loops.items():
            if loop.is_running is False:
                loop.start()
                log.info("loop %s, on Cog %s was started", loop_name, self.name)

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        for loop_name, loop in self.loops.items():
            if loop.is_running() is False:
                loop.start()
                log.info("loop %s, on Cog %s was found to be closed and has been restarted", loop_name, self.name)

    def cog_unload(self):
        for loop_name, loop in self.loops.items():
            if loop.is_running() is True:
                loop.cancel()
                log.info("loop %s, on Cog %s was cancelled", loop_name. self.name)
        log.debug("Cog '%s' UNLOADED!", str(self))

    def dump(self):
        return self.schema.dump(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
