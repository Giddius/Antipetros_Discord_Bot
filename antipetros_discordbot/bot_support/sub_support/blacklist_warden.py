"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Third Party Imports --------------------------------------------------------------------------------->

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import (loadjson, pathmaker, writejson)
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.bot_support.sub_support.sub_support_helper.blacklisted_user_item import BlacklistedUserItem

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


class BlacklistWarden(SubSupportBase):
    """
    Sub Supporter Class for BotSupporter.



    Responsibility: managing and querying the blacklist of Users

    Depend on Sub Supporter:

    Interface:
    """
    blacklist_file = pathmaker(APPDATA["json_data"], "blacklist.json")

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self._blacklisted_user = None

        glog.class_init_notification(log, self)

    @property
    def blacklist_file_exists(self):
        return os.path.isfile(self.blacklist_file)

    def generate_blacklisted_user_hash(self):
        _out = 0
        for item in self._blacklisted_user:
            _out += hash(item)
        return _out

    def get_blacklisted_user(self):
        self._ensure_blacklist_file_exists()
        self._blacklisted_user = [] if self._blacklisted_user is None else self._blacklisted_user
        for item in loadjson(self.blacklist_file):
            blacklisted_user_item = BlacklistedUserItem(warden=self, user_id=item.get('id'), user_name=item.get('name'), command_called=item.get('command_called', 0), notified=item.get('notified', False))
            self._blacklisted_user.append(blacklisted_user_item)

    async def unblacklist_user(self, user_item):
        if isinstance(user_item, int):
            user_item = await self.bot.fetch_user(user_item)
        self._blacklisted_user.remove(user_item)
        self.save()

    async def blacklist_user(self, user):
        if isinstance(user, int):
            user = await self.bot.fetch_user(user)
        new_blacklisted_user_item = BlacklistedUserItem(warden=self, user_id=user.id, user_name=user.name)
        self._blacklisted_user.append(new_blacklisted_user_item)
        self.save()
        return new_blacklisted_user_item

    def save(self):
        _out = []
        for item in self._blacklisted_user:
            _out.append(item.to_dict())
        writejson(_out, self.blacklist_file)

    def _ensure_blacklist_file_exists(self):
        if self.blacklist_file_exists is False:
            writejson([], self.blacklist_file)

    async def command_call_blocked(self, ctx):
        log.debug("command call blocked")
        user = ctx.author
        for item in self._blacklisted_user:
            if item == user:
                log.debug("blacklisted user found")
                item.tried_calling()
                if item.notified is False:
                    log.debug("notifying user")
                    await self.notify(user)
                    log.debug(f"user {ctx.author.name} was notified")
                    item.notified = True
                    self.save()

    async def notify(self, user):
        # TODO: make embed
        await user.send('''You are **__blacklisted__**, you can not use this bot and his commands anymore!

                           If you think this is not correct please contact `@Giddi`!

                           **This is the last time I am answering**''')

    def is_blacklisted(self, other):
        return other in self._blacklisted_user

    async def if_ready(self):
        self.get_blacklisted_user()
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        self.save()
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return BlacklistWarden
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]