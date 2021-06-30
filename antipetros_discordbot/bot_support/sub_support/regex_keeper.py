"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import asyncio
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.exceptions import DuplicateNameError
from antipetros_discordbot.utility.named_tuples import RegexItem
from antipetros_discordbot.utility.gidtools_functions import readit
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
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


class RegexKeeper(SubSupportBase):
    regex_file = APPDATA['regexes_stored.txt']

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.raw_regex_data = ''
        self.regexes = {}
        glog.class_init_notification(log, self)

    def _load_regexes(self):
        self.raw_regex_data = readit(self.regex_file)

    def _process_raw_regexes(self):
        self._load_regexes()
        self.regexes = {}
        for line in self.raw_regex_data.splitlines():
            name, _regex = line.split('=', maxsplit=1)
            name = name.strip()
            _regex = _regex.strip()
            if name not in self.regexes:
                self.regexes[name] = RegexItem(name, _regex)
            else:
                raise DuplicateNameError(name, str(self))

    def _compile_all_regexes(self):
        self._process_raw_regexes()
        for key, value in self.regexes.items():
            self.regexes[key] = value._replace(compiled=re.compile(value.raw))

    def regex(self, regex_name):
        return self.regexes.get(regex_name)

    async def on_ready_setup(self):
        await asyncio.to_thread(self._compile_all_regexes)
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    async def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return RegexKeeper

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
