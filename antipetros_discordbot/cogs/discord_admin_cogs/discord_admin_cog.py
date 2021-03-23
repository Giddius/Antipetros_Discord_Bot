

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
import discord
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin, has_attachments
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "AdministrationCog"
CONFIG_NAME = make_config_name(COG_NAME)
get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class AdministrationCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Commands and methods that help in Administrate the Discord Server.
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.OUTDATED | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:21:10",
                             "8f8fac3c998a0c078515c34712eff238644084f8de06831e9aa13dc36d42978885790242db11e078f4b8f3aa576af177c5143144351d807347e58797eb614027")}
    required_config_data = dedent("""
                                  """)
    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]


# endregion[Properties]

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

    @ auto_meta_info_command(enabled=True)
    @owner_or_admin()
    @log_invoker(log, "critical")
    async def delete_msg(self, ctx, *msgs: discord.Message):
        for msg in msgs:

            await msg.delete()
        await ctx.message.delete()

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(AdministrationCog(bot)))
