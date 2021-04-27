

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags
from typing import TYPE_CHECKING, Any, Union, Optional
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, in_allowed_channels
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
# endregion[Imports]

# region [TODO]

# TODO: Add all special Cog methods

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

# endregion[Constants]


class PurgeMessagesCog(AntiPetrosBaseCog, command_attrs={'hidden': True, "categories": CommandCategory.ADMINTOOLS}):
    """
    Soon
    """

# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}
    required_folder = []
    required_files = []

# endregion[ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        glog.class_init_notification(log, self)


# endregion[Init]
# region [Setup]


    @universal_log_profiler
    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Commands]


    @flags.add_flag("--and-giddi", '-gid', type=bool, default=False)
    @flags.add_flag("--number-of-messages", '-n', type=int, default=99999999999)
    @auto_meta_info_command(cls=AntiPetrosFlagCommand)
    @commands.is_owner()
    @in_allowed_channels()
    async def purge_antipetros(self, ctx: commands.Context, **command_flags):

        def is_antipetros(message):
            if command_flags.get('and_giddi') is False:
                return message.author.id == self.bot.id
            return message.author.id in [self.bot.id, self.bot.creator.id]

        await ctx.channel.purge(limit=command_flags.get('number_of_messages'), check=is_antipetros, bulk=True)
        await ctx.send('done', delete_after=60)
        await delete_message_if_text_channel(ctx)

# endregion[Commands]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion[SpecialMethods]

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(PurgeMessagesCog(bot))

# endregion[Main_Exec]
