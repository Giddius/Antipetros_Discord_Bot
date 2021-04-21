
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
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role, command_enabled_checker, allowed_requester, owner_or_admin

from antipetros_discordbot.utility.gidtools_functions import appendwriteit, clearit, loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_faq_cog import FaqItem

from typing import TYPE_CHECKING, Any, Union, Optional, Callable, Iterable, List, Dict, Set, Tuple, Mapping, Coroutine, Awaitable
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus, CommandCategory
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

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


class FaqCog(AntiPetrosBaseCog, command_attrs={"categories": CommandCategory.ADMINTOOLS, "hidden": True}):

    """
    Creates Embed FAQ items.

    """
# region [ClassAttributes]
    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING | CogMetaStatus.WORKING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {"faq_channel_id": "673410398510383115",
                                            "numbers_background_image": "faq_num_background.png"}}
    required_folder = []
    required_files = []
    q_emoji = "🇶"
    a_emoji = "🇦"


# endregion [ClassAttributes]

# region [Init]


    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.faq_items = {}
        self.ready = False
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def faq_channel(self):
        channel_id = COGS_CONFIG.retrieve(self.config_name, 'faq_channel_id', typus=int, direct_fallback=673410398510383115)
        return self.bot.sync_channel_from_id(channel_id)


# endregion [Properties]

# region [Setup]


    @universal_log_profiler
    async def on_ready_setup(self):
        FaqItem.bot = self.bot
        FaqItem.faq_channel = self.faq_channel
        FaqItem.question_parse_emoji = self.q_emoji
        FaqItem.answer_parse_emoji = self.a_emoji
        FaqItem.config_name = self.config_name
        asyncio.create_task(self.collect_raw_faq_data())
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @commands.Cog.listener(name='on_message')
    @universal_log_profiler
    async def faq_message_added_listener(self, message):
        if self.ready is False:
            return
        channel = message.channel
        if channel is self.faq_channel:
            asyncio.create_task(self.collect_raw_faq_data())

    @commands.Cog.listener(name='on_raw_message_delete')
    @universal_log_profiler
    async def faq_message_deleted_listener(self, payload):
        if self.ready is False:
            return
        channel = self.bot.get_channel(payload.channel_id)
        if channel is self.faq_channel:
            asyncio.create_task(self.collect_raw_faq_data())

    @commands.Cog.listener(name='on_raw_message_edit')
    @universal_log_profiler
    async def faq_message_edited_listener(self, payload):
        if self.ready is False:
            return
        channel = self.bot.get_channel(payload.channel_id)
        if channel is self.faq_channel:
            asyncio.create_task(self.collect_raw_faq_data())


# endregion [Listener]

# region [Commands]

    @auto_meta_info_command()
    @ allowed_channel_and_allowed_role(in_dm_allowed=False)
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


    @universal_log_profiler
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
        max_faq_number = max(self.faq_items)
        if all(_num in self.faq_items for _num in range(1, max_faq_number + 1)):
            log.info('FAQ items collected: %s', max_faq_number)
        else:
            raise KeyError(f"Not all FAQ Items where collected, missing: {', '.join(_num for _num in range(1,max_faq_number+1) if _num not in self.faq_items)}")


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
    bot.add_cog(FaqCog(bot))
