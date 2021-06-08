"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import re
import unicodedata
from typing import Any, Callable
from functools import partial
import discord
from discord.ext import commands, tasks, ipc, flags
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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


class JsonMetaDataProvider:
    gif_folder = APPDATA['gifs']
    stored_attributes_names = ['help',
                               'example',
                               'brief',
                               'description',
                               'short_doc',
                               'usage',
                               'signature',
                               'gif']
    description_split_regex = re.compile(r"args:\n", re.IGNORECASE)
    example_split_regex = re.compile(r"example\:\n", re.IGNORECASE)

    def __init__(self, data_file) -> None:
        self.data_file = pathmaker(data_file)
        if os.path.isfile(self.data_file) is False:
            writejson({}, self.data_file)

    @property
    def all_gifs(self):
        _out = {}
        for file in os.scandir(self.gif_folder):
            if file.is_file() and file.name.casefold().endswith('_command.gif'):
                _out[file.name.casefold().removesuffix('_command.gif')] = pathmaker(file.path)
        return _out

    @property
    def meta_data(self) -> dict:
        return loadjson(self.data_file)

    def get_auto_provider(self, in_object) -> Callable:
        return partial(self.get, in_object)

    def set_auto_provider(self, in_object) -> Callable:
        return partial(self.set, in_object)

    def get(self, in_object, typus: str, fallback=None):

        object_name = in_object.name
        if hasattr(in_object, 'parent') and in_object.parent is not None:
            object_name = f"{in_object.parent.name}.{in_object.name}"

        typus = typus.casefold()
        if typus == 'gif':
            return self.all_gifs.get(object_name.casefold())
        return self.meta_data.get(object_name.casefold(), {}).get(typus, fallback)

    def set(self, in_object, typus: str, value: Any):
        object_name = in_object.name
        if hasattr(in_object, 'parent') and in_object.parent is not None:
            object_name = f"{in_object.parent.name}.{in_object.name}"

        typus = typus.casefold()
        data = self.meta_data
        if object_name.casefold() not in data:
            data[object_name.casefold()] = {}
        data[object_name.casefold()][typus] = value
        self.save(data)

    def save(self, data: dict) -> None:
        writejson(data, self.data_file)

        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
