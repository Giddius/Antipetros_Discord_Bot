"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
from typing import Callable, List, Union
from functools import partial, reduce
from operator import or_
from discord.ext import commands, tasks
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.engine.replacements.command_replacements.command_category import CommandCategory

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


class JsonCategoryProvider:
    """
    Dynamically provides all aliases set for a command.
    """
    category_data_file = pathmaker(APPDATA['documentation'], 'command_categories.json')
    default_category = 'general'

    def __init__(self):
        if os.path.isfile(self.category_data_file) is False:
            writejson({}, self.category_data_file)

    @property
    def category_data(self) -> dict:
        return loadjson(self.category_data_file)

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set_category, command)

    def remove_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.remove, command)

    def get(self, command: Union[str, commands.Command]) -> CommandCategory:
        if isinstance(command, commands.Command):
            command = command.name
        return CommandCategory.deserialize(self.category_data.get(command, 'general'))

    def set_category(self, command: commands.Command, new_category: Union[CommandCategory, str, List[str], List[CommandCategory]]):
        command_name = command.name
        data = self.category_data
        if command_name not in data:
            data[command_name] = []
        if isinstance(new_category, str):
            new_category = CommandCategory.deserialize(new_category)
        elif isinstance(new_category, list):
            if all(isinstance(new_category_item, str) for new_category_item in new_category):
                new_category = CommandCategory.deserialize(new_category)
            elif all(isinstance(new_category_item, CommandCategory) for new_category_item in new_category):
                new_category = reduce(or_, [item for item in new_category])
        data[command_name] += new_category.serialize()
        data[command_name] = list(set(data[command_name]))
        self.save(data)

    def remove(self, command: Union[str, commands.Command], category: Union[str, CommandCategory]):
        raise NotImplementedError()

    def save(self, data: dict) -> None:
        writejson(data, self.category_data_file)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
