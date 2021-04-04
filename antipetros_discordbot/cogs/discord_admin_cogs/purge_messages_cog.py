

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, flags

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, make_full_cog_id
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, in_allowed_channels
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
# endregion[Imports]

# region [TODO]


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
COG_NAME = "PurgeMessagesCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion[Constants]


class PurgeMessagesCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Soon
    """
    cog_id = 685
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:19:50",
                             "b0fabfbd25ed7b45a009737879c2ef61262acce2c3e9043d7b2b27e51f6cd8de27fea94d52e1f97739765b4629d534de76bf28b241c5f27bd96917f3eb8c7e6e")}

    required_config_data = dedent("""
                                  """)

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

    @flags.add_flag("--and-giddi", '-gid', type=bool, default=False)
    @flags.add_flag("--number-of-messages", '-n', type=int, default=99999999999)
    @auto_meta_info_command(enabled=get_command_enabled("purge_antipetros"), cls=flags.FlagCommand)
    @commands.is_owner()
    @in_allowed_channels()
    async def purge_antipetros(self, ctx: commands.Context, **command_flags):

        def is_antipetros(message):
            if command_flags.get('and_giddi') is False:
                return message.author.id == self.bot.id
            return message.author.id in [self.bot.id, self.bot.creator.id]

        await ctx.channel.purge(limit=command_flags.get('number_of_messages'), check=is_antipetros, bulk=True)

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

# region[Main_Exec]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(PurgeMessagesCog(bot)))

# endregion[Main_Exec]
