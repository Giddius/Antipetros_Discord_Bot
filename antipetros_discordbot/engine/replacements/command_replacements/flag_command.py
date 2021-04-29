"""
[summary]

[extended_summary]
"""

# region [Imports]

import gc
import os
import unicodedata
import discord
from discord.ext import commands, tasks, flags, ipc
import gidlogger as glog
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from .base_command import AntiPetrosBaseCommand

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


class AntiPetrosFlagCommand(flags.FlagCommand, AntiPetrosBaseCommand):
    pass


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
