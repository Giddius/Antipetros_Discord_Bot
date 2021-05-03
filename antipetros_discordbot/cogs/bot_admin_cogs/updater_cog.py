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

from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
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


class Updater(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.META}):
    """
    Cog to listen and dispatch Update Signals
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
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    @universal_log_profiler
    async def on_ready_setup(self):
        self.cyclic_update_loop.start()
        self.ready = await asyncio.sleep(0, True)
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        for method, typus_trigger in self.bot.to_update_methods:
            if any(trigger in typus for trigger in typus_trigger):
                await method()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=5)
    async def cyclic_update_loop(self):
        log.info('cyclic update started')
        await self.send_update_signal(UpdateTypus.CYCLIC)


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name="on_guild_channel_delete")
    @universal_log_profiler
    async def guild_structure_changes_listener_remove(self, channel: discord.abc.GuildChannel):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info('pdate Signal %s was send, because Guild channel "%s" was removed', UpdateTypus.GUILD, channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_guild_channel_create")
    @universal_log_profiler
    async def guild_structure_changes_listener_create(self, channel: discord.abc.GuildChannel):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info('Update Signal %s was send, because Guild channel "%s" was created', UpdateTypus.GUILD, channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_guild_channel_update")
    @universal_log_profiler
    async def guild_structure_changes_listener_update(self, before_channel: discord.abc.GuildChannel, after_channel: discord.abc.GuildChannel):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info('Update Signal %s was send, because Guild channel "%s"/"%s" was updated', UpdateTypus.GUILD, before_channel.name, after_channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @ commands.Cog.listener(name="on_guild_update")
    @ universal_log_profiler
    async def guild_update_listener(self, before_guild: discord.Guild, after_guild: discord.Guild):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info('Update Signal %s was send, because Guild was updated', UpdateTypus.GUILD)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_member_join")
    @universal_log_profiler
    async def member_join_listener(self, member: discord.Member):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info("Update Signal %s was send, because a new member joined", UpdateTypus.MEMBERS)
        await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_member_remove")
    @universal_log_profiler
    async def member_remove_listener(self, member: discord.Member):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info("Update Signal %s was send, because a was removed or left", UpdateTypus.MEMBERS)
        await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_member_update")
    @universal_log_profiler
    async def member_roles_changed_listener(self, before: discord.Member, after: discord.Member):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        if set(before.roles) != set(after.roles):
            log.info("Update Signal %s was send, because a members roles changed", UpdateTypus.MEMBERS | UpdateTypus.ROLES)
            await self.send_update_signal(UpdateTypus.MEMBERS | UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_member_update")
    @universal_log_profiler
    async def member_name_changed_listener(self, before: discord.Member, after: discord.Member):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        if before.display_name != after.display_name:
            log.info("Update Signal %s was send, because a members name changed", UpdateTypus.MEMBERS)
            await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_guild_role_create")
    @universal_log_profiler
    async def role_created_listener(self, role: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info("Update Signal %s was send, because the Role %s was created", UpdateTypus.MEMBERS, role.name)
        await self.send_update_signal(UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_guild_role_delete")
    @universal_log_profiler
    async def role_deleted_listener(self, role: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info("Update Signal %s was send, because the Role %s was deleted", UpdateTypus.MEMBERS, role.name)
        await self.send_update_signal(UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_guild_role_update")
    @universal_log_profiler
    async def role_updated_listener(self, before: discord.Role, after: discord.Role):
        if any([self.ready, self.bot.setup_finished]) is False:
            return
        log.info("Update Signal %s was send, because the Role %s was updated", UpdateTypus.MEMBERS, before.name)
        await self.send_update_signal(UpdateTypus.ROLES)

# endregion [Listener]

# region [Commands]


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def send_update_signal(self, typus: UpdateTypus):
        all_tasks = await self.bot.to_all_as_tasks("update", typus=typus)
        if all_tasks:
            await asyncio.wait(all_tasks, return_when="ALL_COMPLETED")

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

    def cog_unload(self):
        self.cyclic_update_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(Updater(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
