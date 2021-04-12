"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timedelta, timezone

# * Third Party Imports --------------------------------------------------------------------------------->
import discord

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import async_date_today
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.sqldata_storager import general_db
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
    exclude_channels = ["website-admin-team",
                        "wiki-mods",
                        "sponsors",
                        "probationary-list",
                        "mute-appeals",
                        "moderator-book",
                        "moderation-team",
                        "event-team",
                        "black-book",
                        "admin-team",
                        "admin-meeting-notes"]
    exclude_categories = ["admin info",
                          "staff rooms",
                          "voice channels"]
    general_db = general_db

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.ready = False

        glog.class_init_notification(log, self)

    async def record_channel_usage(self, msg):
        if self.ready is False:
            return
        if isinstance(msg.channel, discord.DMChannel):
            return
        if msg.author.id == self.bot.id:
            return
        channel = msg.channel
        if channel.name.casefold() not in self.exclude_channels and channel.category.name.casefold() not in self.exclude_categories:
            await self.general_db.insert_channel_use(channel)
            log.info("channel usage recorded for channel '%s'", channel.name)

    async def make_heat_map(self):
        pass

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
        return counter.most_common()

    async def insert_channels_into_db(self):
        for category_channel in self.bot.antistasi_guild.categories:
            if category_channel.name.casefold() not in self.exclude_categories:
                await self.general_db.insert_category_channel(category_channel)
        for text_channel in self.bot.antistasi_guild.text_channels:
            if not text_channel.name.casefold().startswith('ticket-') and text_channel.name.casefold() not in self.exclude_channels:
                await self.general_db.insert_text_channel(text_channel)

    async def if_ready(self):
        await self.insert_channels_into_db()
        self.ready = True
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return ChannelStatistician
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
