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


class BaseCustomHelpCommand(MinimalHelpCommand):
    pass
