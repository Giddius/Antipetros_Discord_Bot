# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from typing import TYPE_CHECKING
import unicodedata
import random
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
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, only_bob
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink

from typing import TYPE_CHECKING
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
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

# endregion[Constants]


class FixedAnswerCog(AntiPetrosBaseCog, command_attrs={"categories": CommandCategory.ADMINTOOLS, "hidden": True}):
    """
    WiP
    """
# region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {"eta_message_title": "When it is ready",
                                            "eta_message_text": "",
                                            "bob_streaming_announcement_channel_name": "announcements"}}

    soon_thumbnails_file = pathmaker(APPDATA["embed_data"], 'soon_thumbnails.json')

    required_folder = []
    required_files = [RequiredFile(soon_thumbnails_file, [], RequiredFile.FileType.JSON)]

# endregion [ClassAttributes]


# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.color = "dark_orange"
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def soon_thumbnails(self):
        if os.path.isfile(self.soon_thumbnails_file) is False:
            writejson([""], self.soon_thumbnails_file)
        return loadjson(self.soon_thumbnails_file)


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command(aliases=['eta', "update"])
    @allowed_channel_and_allowed_role(in_dm_allowed=False)
    async def new_version_eta(self, ctx: commands.Context):
        title = COGS_CONFIG.retrieve(self.config_name, "eta_message_title", typus=str, direct_fallback='When it is ready')
        description = COGS_CONFIG.retrieve(self.config_name, "eta_message_text", typus=str, direct_fallback=embed_hyperlink("Antistasi Milestones on Github", "https://github.com/official-antistasi-community/A3-Antistasi/milestones"))
        embed_data = await self.bot.make_generic_embed(title=title,
                                                       description=await self._spread_out_text(description.strip('"')),
                                                       color="light blue",
                                                       thumbnail=random.choice(self.soon_thumbnails),
                                                       author=None,
                                                       timestamp=None)
        await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
        if ctx.message.reference is not None:
            await delete_message_if_text_channel(ctx)

    @auto_meta_info_command(aliases=['bobdev'])
    @only_bob()
    async def bob_streaming(self, ctx: commands.Context, *, extra_msg: str = None):
        """
        Only for Bob


        Args:
            extra_msg (str, optional): The message you want to add to the embed. Defaults to None.

        Example:
            @AntiPetros bob_streaming This is an extra message and is optional
        """
        announcement_channel_name = COGS_CONFIG.retrieve(self.config_name, 'bob_streaming_announcement_channel_name', typus=str, direct_fallback='announcements')
        announcement_channel = self.bot.channel_from_name(announcement_channel_name)

        bob_member = await self.bot.fetch_antistasi_member(346595708180103170)
        extra_message = "Drop in to see what he's up to and to ask any questions you may have" if extra_msg is None else extra_msg

        embed_data = await self.bot.make_generic_embed(title="Bob Murphy is now streaming Antistasi Development!",
                                                       description=extra_message,
                                                       author={"name": bob_member.display_name, "url": "https://www.twitch.tv/bob_murphy", "icon_url": bob_member.avatar_url},
                                                       color=bob_member.color,
                                                       thumbnail="twitch_logo",
                                                       url="https://www.twitch.tv/bob_murphy")
        await announcement_channel.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await announcement_channel.send("https://www.twitch.tv/bob_murphy", allowed_mentions=discord.AllowedMentions.none())

        # await announcement_channel.send(f"**{bob_member.mention} is now streaming Antistasi Development!**\n\n{extra_message}https://www.twitch.tv/bob_murphy", allowed_mentions=discord.AllowedMentions.none())

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [HelperMethods]

    async def _spread_out_text(self, text: str):
        return f"\n{ZERO_WIDTH}\n".join(line for line in text.splitlines() if line != '')


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
    bot.add_cog(FixedAnswerCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
