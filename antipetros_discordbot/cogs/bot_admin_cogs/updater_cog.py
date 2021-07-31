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
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, AntiPetrosBaseCommand
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

from antipetros_discordbot.engine.replacements.task_loop_replacement import custom_loop
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
                            'cogs_config': {"update_timeout_seconds": "60"}}

    required_files = []
    required_folder = []

# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.typus_on_timeout = {typus: False for typus in UpdateTypus}


# endregion [Init]

# region [Properties]

    @property
    def update_timeout(self):
        return COGS_CONFIG.retrieve(self.config_name, 'update_timeout_seconds', typus=int, direct_fallback=60)

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await super().on_ready_setup()
        self.bot.to_update_methods.append(self.bot.ToUpdateItem(AntiPetrosBaseCommand.alias_data_provider.update_default_alias_chars, [UpdateTypus.CONFIG, UpdateTypus.CYCLIC]))
        self.ready = await asyncio.sleep(0, True)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus=typus)
        for to_update_item in self.bot.to_update_methods:
            if any(trigger in typus for trigger in to_update_item.typus_triggers):
                await to_update_item.function()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @custom_loop(minutes=30)
    async def cyclic_update_loop(self):
        if self.completely_ready is False:
            return
        log.info('cyclic update started')

        await self.send_update_signal(UpdateTypus.CYCLIC)


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name="on_guild_channel_delete")
    async def guild_structure_changes_listener_remove(self, channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        log.info('pdate Signal %s was send, because Guild channel "%s" was removed', UpdateTypus.GUILD, channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_guild_channel_create")
    async def guild_structure_changes_listener_create(self, channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        log.info('Update Signal %s was send, because Guild channel "%s" was created', UpdateTypus.GUILD, channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_guild_channel_update")
    async def guild_structure_changes_listener_update(self, before_channel: discord.abc.GuildChannel, after_channel: discord.abc.GuildChannel):
        if self.completely_ready is False:
            return
        log.info('Update Signal %s was send, because Guild channel "%s"/"%s" was updated', UpdateTypus.GUILD, before_channel.name, after_channel.name)
        await self.send_update_signal(UpdateTypus.GUILD)

    @ commands.Cog.listener(name="on_guild_update")
    async def guild_update_listener(self, before_guild: discord.Guild, after_guild: discord.Guild):
        if self.completely_ready is False:
            return
        log.info('Update Signal %s was send, because Guild was updated', UpdateTypus.GUILD)
        await self.send_update_signal(UpdateTypus.GUILD)

    @commands.Cog.listener(name="on_member_join")
    async def member_join_listener(self, member: discord.Member):
        if self.completely_ready is False:
            return
        log.info("Update Signal %s was send, because a new member joined", UpdateTypus.MEMBERS)
        await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_member_remove")
    async def member_remove_listener(self, member: discord.Member):
        if self.completely_ready is False:
            return
        log.info("Update Signal %s was send, because a was removed or left", UpdateTypus.MEMBERS)
        await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_member_update")
    async def member_roles_changed_listener(self, before: discord.Member, after: discord.Member):
        if self.completely_ready is False:
            return
        if set(before.roles) != set(after.roles):
            log.info("Update Signal %s was send, because a members roles changed", UpdateTypus.MEMBERS | UpdateTypus.ROLES)
            await self.send_update_signal(UpdateTypus.MEMBERS | UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_member_update")
    async def member_name_changed_listener(self, before: discord.Member, after: discord.Member):
        if self.completely_ready is False:
            return
        if before.display_name != after.display_name:
            log.info("Update Signal %s was send, because a members name changed", UpdateTypus.MEMBERS)
            await self.send_update_signal(UpdateTypus.MEMBERS)

    @commands.Cog.listener(name="on_guild_role_create")
    async def role_created_listener(self, role: discord.Role):
        if self.completely_ready is False:
            return
        log.info("Update Signal %s was send, because the Role %s was created", UpdateTypus.MEMBERS, role.name)
        await self.send_update_signal(UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_guild_role_delete")
    async def role_deleted_listener(self, role: discord.Role):
        if self.completely_ready is False:
            return
        log.info("Update Signal %s was send, because the Role %s was deleted", UpdateTypus.MEMBERS, role.name)
        await self.send_update_signal(UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_guild_role_update")
    async def role_updated_listener(self, before: discord.Role, after: discord.Role):
        if self.completely_ready is False:
            return
        log.info("Update Signal %s was send, because the Role %s was updated", UpdateTypus.MEMBERS, before.name)
        await self.send_update_signal(UpdateTypus.ROLES)

    @commands.Cog.listener(name="on_message")
    async def on_message_listener(self, msg: discord.Message):
        if self.completely_ready is False:
            return
        if hasattr(self.bot, 'record_channel_usage'):
            asyncio.create_task(self.bot.record_channel_usage(msg))

# endregion [Listener]

# region [Commands]


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]


    async def remove_typus_from_timeout(self, typus: UpdateTypus):
        await asyncio.sleep(self.update_timeout)
        if typus in self.typus_on_timeout:
            self.typus_on_timeout[typus] = False

    async def send_update_signal(self, typus: UpdateTypus):
        if typus in self.typus_on_timeout and self.typus_on_timeout.get(typus) is True:
            log.debug("%s not sent because it is on timeout", str(typus))
            return
        all_tasks = await self.bot.to_all_as_tasks("update", False, typus=typus)
        if all_tasks:
            await asyncio.wait(all_tasks, return_when="ALL_COMPLETED")
        self.typus_on_timeout[typus] = True
        asyncio.create_task(self.remove_typus_from_timeout(typus))
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
    bot.add_cog(Updater(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
