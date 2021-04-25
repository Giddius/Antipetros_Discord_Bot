"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import asyncio
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import date_today, async_date_today
from antipetros_discordbot.utility.named_tuples import InvokedCommandsDataItem
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.bot_support.sub_support.sub_support_helper.command_stats_dict import CommandStatDict
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.sqldata_storager import general_db
from antipetros_discordbot.engine.replacements.command_replacements.helper import JsonMetaDataProvider
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


class CommandStatistician(SubSupportBase):
    general_db = general_db

    def __init__(self, bot, support):
        self.bot = bot
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.support = support
        glog.class_init_notification(log, self)
        self.after_action()

    async def if_ready(self):
        asyncio.create_task(self.insert_command_data())

        log.debug("'%s' command staff soldier is READY", str(self))

    async def insert_command_data(self):

        cog_objects = []
        command_objects = []
        for cog_name, cog_object in self.bot.cogs.items():
            cog_objects.append(cog_object)
        for command in self.bot.commands:
            if str(command.cog) not in ['GeneralDebugCog']:
                command_objects.append(command)
        await self.general_db.insert_cogs_many(cog_objects)
        await self.general_db.insert_commands_many(command_objects)

    async def get_command_frequency(self, from_datetime: datetime = None, to_datetime: datetime = None, as_counter: bool = True):
        return await self.general_db.get_command_usage(from_datetime=from_datetime, to_datetime=to_datetime, as_counter=as_counter)

    async def get_amount_invoked_overall(self):
        pass

    async def get_todays_invoke_data(self):

        pass

    async def update(self, typus: UpdateTypus):

        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):

        log.debug("'%s' sub_support was RETIRED", str(self))

    def after_action(self):

        async def record_command_invocation(ctx):
            _command = ctx.command
            if _command in ['shutdown', "get_command_stats", None, '']:
                return
            if self.is_debug is False and str(_command.cog) not in ['GeneralDebugCog'] and ctx.channel.name.casefold() not in ['bot-testing']:
                asyncio.create_task(self.general_db.insert_command_usage(_command))
            elif self.is_debug is True:
                asyncio.create_task(self.general_db.insert_command_usage(_command))

            log.debug("command invocations was recorded")

        return self.bot.after_invoke(record_command_invocation)

    def __str__(self) -> str:
        return self.__class__.__name__


def get_class():
    return CommandStatistician

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
