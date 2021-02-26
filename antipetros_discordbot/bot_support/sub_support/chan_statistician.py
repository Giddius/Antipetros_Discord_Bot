"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Third Party Imports --------------------------------------------------------------------------------->
import discord

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import async_date_today
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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
    save_folder = APPDATA['stats']
    temp_folder = APPDATA['temp_files']
    exclude_channels = ["website-admin-team", "wiki-mods", "sponsors", "probationary-list", "mute-appeals", "moderator-book", "moderation-team", "event-team", "black-book", "admin-team", "admin-meeting-notes"]
    exclude_categories = ["admin info", "staff rooms", "voice channels"]
    channel_usage_stats_file = pathmaker(APPDATA['stats'], "channel_usage_stats.json")

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.channel_usage_stats = None

        glog.class_init_notification(log, self)

    async def record_channel_usage(self, msg):
        if isinstance(msg.channel, discord.DMChannel):
            return
        if msg.author.id == self.bot.id:
            return
        channel = msg.channel
        if self.is_debug and channel.name == BASE_CONFIG.get('debug', 'current_testing_channel'):
            return
        self.channel_usage_stats['overall'][channel.name] += 1
        self.channel_usage_stats[await async_date_today()][channel.name] += 1
        log.debug('channel usage was logged, for channel "%s"', channel.name)

    async def make_heat_map(self):
        pass

    async def if_ready(self):
        if os.path.isfile(self.channel_usage_stats_file) is False:
            self.channel_usage_stats = {'overall': {}}
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        if self.channel_usage_stats is not None:
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        self.channel_usage_stats = loadjson(self.channel_usage_stats_file)
        for channel in self.bot.antistasi_guild.channels:
            if channel.name not in self.channel_usage_stats['overall']:
                self.channel_usage_stats['overall'][channel.name] = 0
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        await self.update(typus='time')
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus):
        if typus == 'time':
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
            if await async_date_today() not in self.channel_usage_stats:
                self.channel_usage_stats[await async_date_today()] = {}
            for channel in self.bot.antistasi_guild.channels:
                if channel.name not in self.channel_usage_stats[await async_date_today()]:
                    self.channel_usage_stats[await async_date_today()][channel.name] = 0
            writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        else:
            return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        writejson(self.channel_usage_stats, self.channel_usage_stats_file)
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return ChannelStatistician
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
