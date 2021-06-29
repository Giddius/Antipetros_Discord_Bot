"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timedelta, timezone
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty
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


class TimeKeeper(SubSupportBase):

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug

        glog.class_init_notification(log, self)

    @property
    def start_time(self) -> datetime:
        return datetime.fromisoformat(os.getenv('ANTIPETRO_START_TIME'))

    @ property
    def std_date_time_format(self) -> str:
        return "%Y-%m-%d %H:%M:%S"

    @property
    def std_date_time_format_utc(self) -> str:
        return self.std_date_time_format + ' UTC'

    @property
    def uptime(self):
        now = datetime.now(tz=timezone.utc)
        delta_time = now - self.start_time
        return round(delta_time.total_seconds())

    @property
    def uptime_pretty(self) -> str:
        return alt_seconds_to_pretty(self.uptime)

    async def running_longer_than(self, minutes: int):
        now = datetime.now(tz=timezone.utc)
        if now > (self.start_time + timedelta(minutes=minutes)):
            return True
        return False

    async def on_ready_setup(self):
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return TimeKeeper

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
