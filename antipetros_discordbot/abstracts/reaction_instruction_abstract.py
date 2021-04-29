"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata
from abc import ABC, ABC, abstractmethod
from typing import List


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

# from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog


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


class BaseReactionInstruction(ABC):
    bot = None

    def __init__(self, name: str, emojis: List):
        self.name = name
        self.emojis = emojis

    async def __call__(self, msg: discord.Message):
        if await self.check_trigger(msg) is True:
            for emoji in self.emojis:
                await msg.add_reaction(emoji)

    @abstractmethod
    async def check_trigger(self, message: discord.Message):
        ...

    @classmethod
    @abstractmethod
    async def from_dict(cls, **kwargs):
        ...

    @abstractmethod
    async def to_dict(self):
        ...

    @abstractmethod
    async def get_info_embed(self):
        ...

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.emojis})"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
