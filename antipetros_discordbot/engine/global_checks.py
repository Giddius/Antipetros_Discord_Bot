"""
Conatains Checks that should be applied as global Checks to the Bot itself
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from discord.ext import commands
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


async def user_not_blacklisted(ctx: commands.Context):
    """
    Checks if the User invoking the command is Blacklisted from invoking commands.

    Blocks the command if he is Blacklisted.

    Blacklisted User data is stored in `blacklist.json` and all access to it runs via the sub_supporter `blacklist_warden.py`.

    Args:
        bot `discord.ext.commands.Bot`: Bot instance to access the sub_supporter `blacklist_warden.py`.
        logger `logging.Logger`: Logger to log the invokation try of the blacklisted User.

    """
    bot = ctx.bot
    if bot.is_blacklisted(ctx.author):
        log.warning('Tried invocation by blacklisted user: "%s", id: "%s"', ctx.author.name, str(ctx.author.id))
        await bot.command_call_blocked(ctx)

        return False

    return True


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
