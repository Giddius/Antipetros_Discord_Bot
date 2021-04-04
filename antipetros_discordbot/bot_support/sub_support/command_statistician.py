"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import date_today, async_date_today
from antipetros_discordbot.utility.named_tuples import InvokedCommandsDataItem
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.bot_support.sub_support.sub_support_helper.command_stats_dict import CommandStatDict
from antipetros_discordbot.utility.enums import UpdateTypus
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
    save_folder = APPDATA['stats']
    cog_invoked_stats_file = pathmaker(save_folder, 'cog_invoked_stats.json')
    command_invoked_stats_file = pathmaker(save_folder, 'command_invoked_stats.json')

    def __init__(self, bot, support):
        self.bot = bot
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.support = support
        self.cog_invoked_stats = None
        self.command_invoked_stats = None
        self.stats_holder = None
        glog.class_init_notification(log, self)
        self.after_action()

    def cog_name_list(self):
        return [str(cog_object) for cog_name, cog_object in self.bot.cogs.items()]

    def command_name_list(self):
        return [command.name for command in self.bot.all_cog_commands()] + [self.bot.help_invocation]

    async def if_ready(self):
        if self.stats_holder is None:
            self.stats_holder = []
            if self.cog_invoked_stats is not None and self.cog_invoked_stats.is_empty is False:
                self.cog_invoked_stats.save_data()
            if self.command_invoked_stats is not None and self.command_invoked_stats.is_empty is False:
                self.command_invoked_stats.save_data()
                self.command_invoked_stats.save_overall()
            self.cog_invoked_stats = CommandStatDict(self.cog_invoked_stats_file, self.cog_name_list)
            self.command_invoked_stats = CommandStatDict(self.command_invoked_stats_file, self.command_name_list)
            self.stats_holder.append(self.cog_invoked_stats)
            self.stats_holder.append(self.command_invoked_stats)
            log.debug("'%s' command staff soldier was READY", str(self))

    async def get_amount_invoked_overall(self):
        return self.command_invoked_stats.sum_data.get('overall', {}).get('successful', 0)

    async def get_todays_invoke_data(self):
        overall_data = self.command_invoked_stats.sum_data.get(date_today())
        data = '\n'.join(f"**{key}**: *{str(value)}*" for key, value in overall_data.items() if value != 0)
        overall_item = InvokedCommandsDataItem('overall', await async_date_today(), data)

        cogs_data = self.cog_invoked_stats.get(date_today())
        data = '\n'.join(f"**{key}**: successful = *{value.get('successful')}* | unsuccessful = *{value.get('unsuccessful')}*" for key, value in cogs_data.items() if any(subvalue != 0 for subkey, subvalue in value.items()))

        cogs_item = InvokedCommandsDataItem('cogs', await async_date_today(), data)

        commands_data = self.command_invoked_stats.get(date_today())
        data = '\n'.join(f"**{key}**: successful = *{value.get('successful')}* | unsuccessful = *{value.get('unsuccessful')}*" for key, value in commands_data.items() if value.get('successful') != 0 or value.get('unsuccessful') != 0)
        commands_item = InvokedCommandsDataItem('commands', await async_date_today(), data)

        return overall_item, cogs_item, commands_item

    async def update(self, typus: UpdateTypus):
        if UpdateTypus.DATE in typus:
            self.command_invoked_stats.save_data()
            self.command_invoked_stats.save_overall()
            self.command_invoked_stats.initialize_data()
        else:
            return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        for holder in self.stats_holder:
            holder.save_data()
        self.command_invoked_stats.save_overall()
        log.debug("'%s' sub_support was RETIRED", str(self))

    def after_action(self):

        async def record_command_invocation(ctx):
            _command = ctx.command
            _cog = _command.cog
            _command = _command.name
            _cog = str(_cog)
            if _command in ['shutdown', "get_command_stats", None, '']:
                return
            if _cog in [None]:
                return

            self.cog_invoked_stats.add_tick(_cog, ctx.command_failed)
            self.command_invoked_stats.add_tick(_command, ctx.command_failed)
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
