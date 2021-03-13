from discord.ext.commands import Command
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writeit, loadjson, writejson
from typing import List, Dict, Set, Tuple, Union
import os
import discord
from enum import Enum, Flag, auto, unique
from discord.ext import commands, tasks
from discord.ext.commands import MinimalHelpCommand


APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')


@unique
class HelpLimitedTo(Enum):
    CHANNELS = auto()
    DM = auto()
    NOT_LIMITED = auto()

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.casefold()
        value = value.casefold()
        if value in ['channels', 'channel']:
            return cls.CHANNELS
        if value in ['dm', 'dms', 'pm', 'pms', 'direct', 'direct messages', 'private', 'private messages']:
            return cls.DM
        if value in [None, 'none', 'all']:
            return cls.NOT_LIMITED


class VerifyBy(Flag):
    ROLES = auto()
    CHANNELS = auto()
    DM_ALLOWED = auto()


class BaseCustomHelpCommand(MinimalHelpCommand):
    bot = None
    gif_folder = APPDATA['gifs']
    gif_suffix = '_command.gif'
    command_help_data_file = pathmaker(APPDATA['documentation'], 'command_help_data.json')
    config_name = 'help_settings'

    def __init__(self, sort_commands: bool = True, **options):
        super().__init__(sort_commands=sort_commands, **options)
        self.verify_by = None

    @property
    def limit_to(self) -> HelpLimitedTo:
        return HelpLimitedTo(BASE_CONFIG.retrieve(self.config_name, 'limited_to', typus=str, direct_fallback=None))

    @property
    def show_hidden(self) -> bool:
        return BASE_CONFIG.retrieve(self.config_name, 'show_hidden', typus=bool, direct_fallback=False)

    @property
    def dm_help(self) -> bool:
        return self.limit_to is HelpLimitedTo.DM

    @property
    def available_gifs(self) -> Dict[str, str]:
        """
        all gifs in the gif folder, that have the gif_suffix, as dictionary.

        keys are file names stripped of the suffix and casefolded.

        """
        gifs = {}
        for file in os.scandir(self.gif_folder):
            if file.is_file() and file.name.endswith(self.gif_suffix):
                gifs[file.name.removesuffix(self.gif_suffix).casefold()] = pathmaker(file.path)
        return gifs

    @property
    def command_help_data(self) -> Dict[str, dict]:
        try:
            return loadjson(self.command_help_data_file)
        except FileNotFoundError:
            writejson({}, self.command_help_data_file)
            return {}

    async def get_command_gif_file(self, command_name: str) -> Union[discord.File, None]:
        """
        Return gif of command, as discord-File if the give is available, or return None if not.

        Args:
            command_name (str): name of the command

        Returns:
            Union[discord.File, None]: gif as discord File or None
        """
        path = self.available_gifs.get(command_name.casefold(), None)
        if path is not None:
            return discord.File(path)
        return None

    async def get_command_help_attribute(self, command_name: str, attribute_name: str) -> Union[str, None]:
        return self.command_help_data.get(command_name, {}).get(attribute_name, None)
