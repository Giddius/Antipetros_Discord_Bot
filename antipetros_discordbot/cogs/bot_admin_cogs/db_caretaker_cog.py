# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from typing import TYPE_CHECKING
import asyncio
import unicodedata

# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.misc import loop_starter
from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


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
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion [Constants]


class DbCaretakerCog(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.META}):
    """
    Cog to handle mostly background and update Task for the Database.
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING

    required_config_data = {'base_config': {},
                            'cogs_config': {}}

    required_files = []
    required_folder = []

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.db = general_db
        self.color = "gray"


# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        await super().on_ready_setup()

        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus=typus)
        if typus in [UpdateTypus.ALIAS, UpdateTypus.CONFIG]:
            await self.bot.insert_command_data()

        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(hours=6)
    async def scheduled_vacuum(self):
        if self.completely_ready is False:
            return
        asyncio.create_task(self.db.aio_vacuum(), name='db_vacuum')
        log.info("%s was scheduled vacuumed", str(self.db))

# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name="on_guild_channel_delete")
    async def guild_structure_changes_listener_remove(self, channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        await self.bot.insert_channels_into_db()
        log.info('updated channels in %s, because Guild channel "%s" was removed', self.db, channel.name)

    @commands.Cog.listener(name="on_guild_channel_create")
    async def guild_structure_changes_listener_create(self, channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        await self.bot.insert_channels_into_db()
        log.info('updated channels in %s, because Guild channel "%s" was created', self.db, channel.name)

    @commands.Cog.listener(name="on_guild_channel_update")
    async def guild_structure_changes_listener_update(self, before_channel: discord.abc.GuildChannel, after_channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        await self.bot.insert_channels_into_db()
        log.info('updated channels in %s, because Guild channel "%s"/"%s" was updated', self.db, before_channel.name, after_channel.name)

    @commands.Cog.listener(name="on_guild_update")
    async def guild_update_listener(self, before_guild: discord.Guild, after_guild: discord.Guild):
        if self.completely_ready is False:
            return
        await self.bot.insert_channels_into_db()
        log.info('updated channels in %s, because Guild was updated', self.db)


# endregion [Listener]

# region [Commands]


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    # def cog_unload(self):
    #     log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(DbCaretakerCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
