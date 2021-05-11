

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from time import time
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
import asyncio
import json
from pprint import pprint, pformat
from dotenv import load_dotenv
from datetime import datetime
import shutil
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory

# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands, flags, tasks
from emoji import demojize, emojize, emoji_count
from emoji.unicode_codes import EMOJI_UNICODE_ENGLISH
from webdav3.client import Client
from icecream import ic
from typing import TYPE_CHECKING
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from dateparser import parse as date_parse
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import antipetros_repo_rel_path, async_seconds_to_pretty_normal, generate_bot_data
from antipetros_discordbot.utility.checks import has_attachments, only_giddi
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker, writejson, loadjson, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosBaseGroup, CommandCategory, auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import create_emoji_custom_name, normalize_emoji
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.data_gathering import gather_data
from antipetros_discordbot.utility.exceptions import NotAllowedChannelError
from antipetros_discordbot.utility.converters import CogConverter, CommandConverter
from pyyoutube import Api
from inspect import cleandoc, getdoc, getmembers, getsource, getsourcefile
from antipetros_discordbot.utility.sqldata_storager import general_db
from marshmallow import Schema, fields
from rich import inspect as rinspect
from antipetros_discordbot.engine.replacements.helper.help_embed_builder import HelpEmbedBuilder
from antipetros_discordbot.schemas.bot_schema import AntiPetrosBotSchema
from antipetros_discordbot.auxiliary_classes.server_item import ServerItem

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
# endregion [Imports]

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

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]


class GeneralDebugCog(AntiPetrosBaseCog, command_attrs={'hidden': True}):
    """
    Cog for debug or test commands, should not be enabled fo normal Bot operations.
    """

    public = False
    meta_status = CogMetaStatus.WORKING | CogMetaStatus.OPEN_TODOS | CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.NEEDS_REFRACTORING | CogMetaStatus.DOCUMENTATION_MISSING | CogMetaStatus.FOR_DEBUG

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.bob_user = None
        self.antidevtros_member = None
        self.antipetros_member = None
        self.edit_embed_message = None
        self.general_db = general_db
        self.server_item_1 = ServerItem('mainserver_1', "nae-ugs1.armahosts.com:2312", 'Mainserver_1')
        glog.class_init_notification(log, self)

    async def on_ready_setup(self):

        self.bob_user = await self.bot.fetch_antistasi_member(346595708180103170)
        for member in self.bot.antistasi_guild.members:
            if member.bot is True:
                if member.display_name.casefold() == 'antidevtros':
                    self.antidevtros_member = member

                elif member.display_name.casefold() == 'antipetros':
                    self.antipetros_member = member
                else:
                    if self.antidevtros_member is not None and self.antipetros_member is not None:
                        break
        await generate_bot_data(self.bot, self.antipetros_member)

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

    @auto_meta_info_command()
    async def dump_bot(self, ctx: commands.Context):
        schema = AntiPetrosBotSchema()
        data = schema.dump(self.bot)
        with open('bot_dump.json', 'w') as f:
            f.write(json.dumps(data, default=str, sort_keys=True, indent=4))

        await ctx.send('done')

    @auto_meta_info_command()
    async def cached_msgs(self, ctx: commands.Context):
        data = list(map(lambda x: x.content, self.bot.cached_messages))
        writejson(data, "cached_msgs.json")

    @auto_meta_info_command()
    async def save_msg(self, ctx: commands.Context, channel: discord.TextChannel, message_id: int):
        msg = await channel.fetch_message(message_id)
        with open(str(message_id) + ".txt", 'w', encoding='utf-8', errors='ignore') as f:
            f.write(msg.content)
        writejson(msg.content, str(message_id) + '.json')
        await ctx.send('done')

    @auto_meta_info_command()
    async def check_server_item(self, ctx: commands.Context):
        await ctx.send(str(await self.server_item_1.get_info()))

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

    async def cog_check(self, ctx):
        if ctx.author.id == 576522029470056450:
            return True
        return False


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(GeneralDebugCog(bot))
