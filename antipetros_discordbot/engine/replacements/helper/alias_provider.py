"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
from typing import Callable, Callable, List, Tuple, Union
from functools import partial
from discord.ext import commands, tasks
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from string import punctuation
import re
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class JsonAliasProvider:
    """
    Dynamically provides all aliases set for a command.
    """
    alias_data_file = pathmaker(APPDATA['documentation'], 'command_aliases.json')
    base_config = ParaStorageKeeper.get_config('base_config')
    punctuation_regex = re.compile(rf"[{re.escape(punctuation)}]")
    default_alias_chars = BASE_CONFIG.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')

    def __init__(self):
        if os.path.isfile(self.alias_data_file) is False:
            writejson({}, self.alias_data_file)

    @classmethod
    async def update_default_alias_chars(cls):
        cls.default_alias_chars = BASE_CONFIG.retrieve('command_meta', 'base_alias_replacements', typus=List[str], direct_fallback='-')

    @property
    def custom_alias_data(self) -> dict:
        return loadjson(self.alias_data_file)

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set_alias, command)

    def remove_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.remove, command)

    def get(self, command: Union[str, commands.Command], extra_aliases: Union[List, Tuple] = None) -> list[str]:
        if isinstance(command, commands.Command):
            command = command.name
        all_aliases = [] if extra_aliases is None else list(extra_aliases)
        all_aliases = all_aliases + self._get_default_aliases(command) + self._get_custom_aliases(command)
        return list(set(map(lambda x: x.casefold(), all_aliases)))

    def _get_default_aliases(self, command: Union[str, commands.Command]) -> List[str]:
        if isinstance(command, commands.Command):
            command = command.name
        return [command.replace('_', char) for char in self.default_alias_chars if command.replace('_', char) != command]

    def _get_custom_aliases(self, command: Union[str, commands.Command]) -> List[str]:
        if isinstance(command, commands.Command):
            command = command.name
        return self.custom_alias_data.get(command.casefold(), [])

    def set_alias(self, command: commands.Command, new_alias: str):
        new_alias = new_alias.casefold()

        command_name = command.name.casefold()
        data = loadjson(self.alias_data_file)
        if command_name not in data:
            data[command_name] = []
        pre_size = len(data[command_name])
        data[command_name].append(new_alias)
        data[command_name] = list(set(map(lambda x: x.casefold(), data[command_name])))
        post_size = len(data[command_name])
        self.save(data)
        command.cog.bot.refresh_command(command)
        if post_size > pre_size:
            return True
        else:
            return False

    def remove(self, command: Union[str, commands.Command], alias: str):
        alias = alias.casefold()
        if isinstance(command, commands.Command):
            command = command.name
        command = command.casefold()
        data = loadjson(self.alias_data_file)
        if command not in data:
            return False
        if alias not in data[command]:
            return False
        data[command].remove(alias)
        self.save(data)

    def save(self, data: dict) -> None:
        writejson(data, self.alias_data_file)

    def get_best_alias(self, command: commands.Command) -> str:
        weighted_aliases = sorted(command.aliases + [command.name], key=self._alias_weighting)
        return weighted_aliases[0]

    def _alias_weighting(self, alias) -> int:
        alias_length = len(self.punctuation_regex.sub('', alias))
        punctuation_characters = self.punctuation_regex.findall(alias)
        if not punctuation_characters:
            punctuation_characters = ['']
        amount_punctuation = len([char for char in punctuation_characters if char])

        return self._alias_weighting_calculation(alias_length, punctuation_characters, amount_punctuation)

    def _alias_weighting_calculation(self, alias_length: int, punctuation_characters: List[str], amount_punctuation: int) -> int:

        _out = alias_length + amount_punctuation

        return _out


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
