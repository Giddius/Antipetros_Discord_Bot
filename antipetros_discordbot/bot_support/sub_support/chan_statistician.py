"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timedelta, timezone
import asyncio
# * Third Party Imports --------------------------------------------------------------------------------->
import discord

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.sqldata_storager import general_db
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
    from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class ChannelStatistician(SubSupportBase):
    exclude_channels = {"website-admin-team",
                        "wiki-mods",
                        "sponsors",
                        "probationary-list",
                        "mute-appeals",
                        "moderator-book",
                        "moderation-team",
                        "event-team",
                        "black-book",
                        "admin-team",
                        "admin-meeting-notes"}
    exclude_categories = {"admin info",
                          "staff rooms",
                          "voice channels"}
    general_db = general_db

    def __init__(self, bot: "AntiPetrosBot", support: "BotSupporter"):
        self.bot = bot
        self.support = support

        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.ready = False

        glog.class_init_notification(log, self)

    async def record_channel_usage(self, msg: discord.Message):
        if all(msg.content.startswith(prfx) is False for prfx in await self.bot.get_prefix(msg)):
            asyncio.create_task(self._channel_usage_to_db(msg))

    async def _channel_usage_to_db(self, msg: discord.Message):
        channel = msg.channel
        if self.bot.setup_finished is False:
            return
        if await asyncio.sleep(0, msg.author.bot) is True:
            return
        if await asyncio.sleep(0, isinstance(msg.channel, discord.DMChannel)) is True:
            return
        if await asyncio.sleep(0, channel.name.casefold()) in self.exclude_channels:
            return
        if await asyncio.sleep(0, channel.category.name.casefold()) in self.exclude_categories:
            return

        asyncio.create_task(self.general_db.insert_channel_use(channel))
        log.info("channel usage recorded for channel '%s'", channel.name)

    async def make_heat_map(self):
        return NotImplemented

    async def get_usage_stats(self, scope: str = "all"):
        now = datetime.now(tz=timezone.utc)
        scope_mapping = {'day': (now - timedelta(days=1), None),
                         'week': (now - timedelta(weeks=1), None),
                         'month': (now - timedelta(weeks=4), None),
                         'year': (now - timedelta(weeks=52), None),
                         'all': (None, None)}
        arguments = scope_mapping.get(scope)
        result_item = await self.general_db.get_channel_usage(arguments[0], arguments[1])
        await result_item.convert_data_to_channels(self.bot)
        counter = await result_item.get_as_counter()
        return await asyncio.to_thread(counter.most_common)

    async def insert_channels_into_db(self):
        category_channels_data = []
        text_channels_data = []
        all_channels = await self.bot.antistasi_guild.fetch_channels()
        all_channels_map = {channel.type: [] for channel in all_channels}
        for channel_type in all_channels_map:
            all_channels_map[channel_type] += [channel for channel in all_channels if channel.type is channel_type]

        for category_channel in all_channels_map.get(discord.ChannelType.category):
            if category_channel.name.casefold() not in self.exclude_categories:
                category_channels_data.append(category_channel)
        for text_channel in all_channels_map.get(discord.ChannelType.text):
            if not text_channel.name.casefold().startswith('ticket-') and text_channel.name.casefold() not in self.exclude_channels:
                text_channels_data.append(text_channel)
        await self.general_db.insert_category_channels(category_channels_data)
        await self.general_db.insert_text_channels(text_channels_data)
        existing_category_ids = {category.id for category in all_channels_map.get(discord.ChannelType.category)}
        for category_id in await self.general_db.get_category_channel_ids():
            if category_id not in existing_category_ids:
                await self.general_db.update_category_channel_deleted(category_id)
        existing_text_channel_ids = {channel.id for channel in all_channels_map.get(discord.ChannelType.text)}
        for text_channel_id in await self.general_db.get_text_channel_ids():
            if text_channel_id not in existing_text_channel_ids:
                await self.general_db.update_text_channel_deleted(text_channel_id)

    async def on_ready_setup(self):
        asyncio.create_task(self.insert_channels_into_db())
        self.ready = True
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        log.debug("'%s' sub_support was UPDATED", str(self))

    async def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return ChannelStatistician
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
