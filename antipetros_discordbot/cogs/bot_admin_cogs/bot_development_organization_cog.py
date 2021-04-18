from __future__ import annotations

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from configparser import ConfigParser, NoOptionError, NoSectionError
from collections import namedtuple
from typing import List
from datetime import datetime, timedelta
from textwrap import dedent
from pprint import pformat
from io import BytesIO
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands
from typing import TYPE_CHECKING
from asyncstdlib.builtins import map as amap

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writejson, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_config_cog import AddedAliasChangeEvent

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
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
COG_NAME = "BotDevOrgCog"
CONFIG_NAME = make_config_name(COG_NAME)

# endregion[Constants]

# region [Helper]

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Helper]


class BotDevOrgCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Cog to help in the organization of the continuos Bot development. Saving Proposals, discussions, ideas...

    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME
    dev_org_folder = APPDATA['bot_development_organization']
    dev_org_files_folder = APPDATA['bot_development_organization_files']
    ideas_file = pathmaker(dev_org_folder, 'bot_ideas.json')
    discussion_file = pathmaker(dev_org_folder, 'bot_discussion.json')
    proposals_file = pathmaker(dev_org_folder, 'proposals.json')
    bot_development_channel_id = 704838990011826197

    docattrs = {'show_in_readme': False,
                'is_ready': CogState.OPEN_TODOS | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING,
                'extra_description': dedent("""
                                            """).strip(),
                'caveat': None}

    required_config_data = dedent("""

                                """)
    # endregion[ClassAttributes]

    # region [Init]

    def __init__(self, bot: AntiPetrosBot):
        self.bot = bot
        self.giddi = self.bot.creator.member_object
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):
        """
        standard setup async method.
        The Bot calls this method on all cogs when he has succesfully connected.
        """

        for file in [self.ideas_file, self.discussion_file, self.proposals_file]:
            if os.path.isfile(file) is False:
                writejson([], file)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Properties]


    @property
    def bot_development_channel(self):
        return self.bot.sync_channel_from_id(self.bot_development_channel_id)


# endregion[Properties]

# region [HelperMethods]


# endregion [HelperMethods]

# region [Listener]

    async def _scan_bot_development_checks(self, msg: discord.Message):
        if msg.channel is not self.bot_development_channel:
            return False
        if msg.author is not self.giddi:
            return False
        if not msg.content.startswith('__#'):
            return False
        return True

    @commands.Cog.listener(name='on_message')
    async def scan_bot_development(self, msg: discord.Message):
        if await self._scan_bot_development_checks(msg) is False:
            return

# endregion[Listener]

# region [Commands]


# endregion [Commands]

# region [Helper]


# endregion[Helper]

# region [SpecialMethods]


    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(BotDevelopmentOrganizationCog(bot)))
