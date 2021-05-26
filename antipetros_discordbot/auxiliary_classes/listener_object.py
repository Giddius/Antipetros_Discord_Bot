"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata

from typing import Callable, Union
from inspect import getdoc, getsource, getsourcefile, getsourcelines


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks, flags, ipc

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog
from antipetros_discordbot.utility.event_data import ListenerEvents
from antipetros_discordbot.utility.misc import get_github_line_link
from antipetros_discordbot.utility.gidtools_functions import pathmaker
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class ListenerObject:
    github_base_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/blob/development/"

    def __init__(self, event: Union[str, ListenerEvents], method: Callable, cog: commands.Cog = None):
        self.event = ListenerEvents(event) if isinstance(event, str) else event
        self.method = method
        self.name = self.method.__name__
        self._cog = cog

    @property
    def description(self):
        return getdoc(self.method)

    @property
    def code(self) -> str:
        return getsource(self.method)

    @property
    def file(self):
        return pathmaker(getsourcefile(self.cog.__class__))

    @property
    def source_lines(self):
        return getsourcelines(self.method)

    @property
    def github_link(self):
        return get_github_line_link(self.github_base_url, self.file, self.source_lines)

    @property
    def cog(self) -> commands.Cog:
        if self._cog is not None:
            return self._cog
        # module = getmodule(self.method)
        # for name, class_object in getmembers(module, isclass):
        #     if class_object.__module__ == module.__name__ and isinstance(class_object, commands.Cog):
        #         self._cog = clas
        #         return class_object


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
