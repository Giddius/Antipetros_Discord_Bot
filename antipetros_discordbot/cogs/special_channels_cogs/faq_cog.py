
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple

import random
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
from jinja2 import BaseLoader, Environment
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import CogConfigReadOnly, make_config_name, minute_to_second
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester, owner_or_admin

from antipetros_discordbot.utility.gidtools_functions import appendwriteit, clearit, loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_faq_cog import FaqItem
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

COG_NAME = 'FaqCog'

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class FaqCog(commands.Cog, command_attrs={'name': COG_NAME, "description": ""}):

    """
    Creates Embed FAQ items.

    """
# region [ClassAttributes]
    config_name = CONFIG_NAME
    q_emoji = "🇶"
    a_emoji = "🇦"

    docattrs = {'show_in_readme': True,
                "is_ready": (CogState.WORKING | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 03:33:42",
                             "6e72c93ce50bf8f6a95d55b1a8c1c8b51588f5a804902c2ba57c9f5b2afe3f35b31b5bc52d3f6a71b1a887e82345453771c797b53e41780e4beaff3388b64331")}

    required_config_data = dedent("""
                                        faq_channel_id = 673410398510383115
                                        numbers_background_image = faq_num_background.png
                                        """)


# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot):

        self.bot = bot
        self.support = self.bot.support
        self.faq_items = {}
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def faq_channel(self):
        channel_id = COGS_CONFIG.retrieve(self.config_name, 'faq_channel_id', typus=int, direct_fallback=673410398510383115)
        return self.bot.sync_channel_from_id(channel_id)


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        FaqItem.bot = self.bot
        FaqItem.question_parse_emoji = self.q_emoji
        FaqItem.answer_parse_emoji = self.a_emoji
        FaqItem.config_name = self.config_name
        await self.collect_raw_faq_data()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


    @commands.Cog.listener(name='on_message')
    async def faq_message_added_listener(self, message):
        channel = message.channel
        if channel is self.faq_channel:
            await self.collect_raw_faq_data()

    @commands.Cog.listener(name='on_raw_message_delete')
    async def faq_message_deleted_listener(self, payload):
        channel = channel = self.bot.get_channel(payload.channel_id)
        if channel is self.faq_channel:
            await self.collect_raw_faq_data()

    @commands.Cog.listener(name='on_raw_message_edit')
    async def faq_message_edited_listener(self, payload):
        channel = channel = self.bot.get_channel(payload.channel_id)
        if channel is self.faq_channel:
            await self.collect_raw_faq_data()


# endregion [Listener]

# region [Commands]


    @auto_meta_info_command(enabled=get_command_enabled('post_faq_by_number'))
    @ allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def post_faq_by_number(self, ctx, faq_numbers: commands.Greedy[int]):
        """
        Posts an FAQ as an embed on request.

        Either as an normal message or as an reply, if the invoking message was also an reply.

        Deletes invoking message

        Args:
            faq_numbers (commands.Greedy[int]): minimum one faq number to request, maximum as many as you want seperated by one space (i.e. 14 12 3)
        """

        for faq_number in faq_numbers:

            if faq_number not in self.faq_items:
                await ctx.send(f'No FAQ Entry with the number {faq_number}')
                continue
            faq_item = self.faq_items.get(faq_number)
            embed_data = await faq_item.to_embed_data()
            if ctx.message.reference is not None:

                await ctx.send(**embed_data, reference=ctx.message.reference, allowed_mentions=discord.AllowedMentions.none())
            else:
                await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        await ctx.message.delete()


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]


    async def collect_raw_faq_data(self):
        channel = self.faq_channel
        self.faq_items = {}
        async for message in channel.history(limit=None, oldest_first=True):
            content = message.content
            created_at = message.created_at
            jump_url = message.jump_url
            image = None
            if len(message.attachments) > 0:
                image = message.attachments[0]
            faq_item = FaqItem(content, created_at, jump_url, image)
            self.faq_items[faq_item.number] = faq_item
            log.debug(f"collected faq item {faq_item.number}")
        log.info('Updated all FAQ items')


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
    bot.add_cog(attribute_checker(FaqCog(bot)))