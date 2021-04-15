"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from datetime import datetime
from typing import List
import random
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands
import arrow
from humanize import naturaltime
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, pickleit
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.checks import owner_or_admin, log_invoker
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup
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
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class EssentialCommandsKeeper(SubSupportBase):
    cog_import_base_path = BASE_CONFIG.get('general_settings', 'cogs_location')
    shutdown_message_pickle_file = pathmaker(APPDATA['temp_files'], 'last_shutdown_message.pkl')
    goodbye_quotes_file = APPDATA['goodbye_quotes.json']

    def __init__(self, bot: commands.Bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.shutdown_message_pickle = None

        glog.class_init_notification(log, self)

    @property
    def shutdown_message_channel(self):
        channel_name = BASE_CONFIG.retrieve("shutdown_message", "channel_name", typus=str, direct_fallback='bot-commands')
        return self.bot.sync_channel_from_name(channel_name)

    async def shutdown_mechanic(self):
        try:
            started_at = self.support.start_time

            started_at_string = arrow.get(started_at).format('YYYY-MM-DD HH:mm:ss')
            online_duration = naturaltime(datetime.utcnow() - started_at).replace(' ago', '')

            embed = await self.bot.make_generic_embed(title=random.choice(loadjson(self.goodbye_quotes_file)),
                                                      description=f'{self.bot.display_name} is shutting down.',
                                                      image=BASE_CONFIG.retrieve('shutdown_message', 'image', typus=str, direct_fallback="https://i.ytimg.com/vi/YATREe6dths/maxresdefault.jpg"),
                                                      type=self.support.embed_types_enum.Image,
                                                      thumbnail="red_chain",
                                                      fields=[self.support.field_item(name='Online since', value=str(started_at_string), inline=False), self.support.field_item(name='Online for', value=str(online_duration), inline=False)])
            channel = self.shutdown_message_channel
            last_shutdown_message = await channel.send(**embed)
            pickleit({"message_id": last_shutdown_message.id, "channel_id": last_shutdown_message.channel.id}, self.shutdown_message_pickle_file)

        except Exception as error:
            log.error(error, exc_info=True)
        finally:
            await self.bot.close()

    async def if_ready(self):

        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return EssentialCommandsKeeper
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
