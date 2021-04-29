"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import re
import unicodedata

from typing import Any, Callable, Callable, Union
from functools import partial


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks, ipc, flags

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
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
    data_file = pathmaker(APPDATA['documentation'], 'command_meta_data.json')
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

    def __init__(self) -> None:
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

    def get_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.get, command)

    def set_auto_provider(self, command: commands.Command) -> Callable:
        return partial(self.set, command)

    def get(self, command: commands.Command, typus: str, fallback=None):

        command_name = command.name
        if command.parent is not None:
            command_name = f"{command.parent.name}.{command.name}"

        typus = typus.casefold()
        if typus == 'gif':
            return self.all_gifs.get(command_name.casefold())
        return self.meta_data.get(command_name.casefold(), {}).get(typus, fallback)

    def set(self, command: commands.Command, typus: str, value: Any):
        command_name = command.name
        if command.parent is not None:
            command_name = f"{command.parent.name}.{command.name}"
        typus = typus.casefold()
        data = self.meta_data
        if command_name.casefold() not in data:
            data[command_name.casefold()] = {}
        data[command_name.casefold()][typus] = value
        self.save(data)

    def save(self, data: dict) -> None:
        writejson(data, self.data_file)


        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
