from discord.ext.commands import Command
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from typing import List
import os


APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
