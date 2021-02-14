"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.exceptions import DuplicateNameError
from antipetros_discordbot.utility.named_tuples import RegexItem
from antipetros_discordbot.utility.gidtools_functions import readit, loadjson, writejson, writeit, pathmaker
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from typing import TYPE_CHECKING

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


class AntistasiInformer(SubSupportBase):
    general_data_file = pathmaker(APPDATA['fixed_data'], 'general_data.json')

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug

        glog.class_init_notification(log, self)

    @property
    def general_data(self):
        return loadjson(self.general_data_file)

    @ property
    def antistasi_guild(self):
        return self.bot.get_guild(self.general_data.get('antistasi_guild_id'))

    async def retrieve_antistasi_member(self, user_id):
        return await self.antistasi_guild.fetch_member(user_id)

    async def channel_from_name(self, channel_name):
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

    async def channel_from_id(self, channel_id: int):
        return {channel.id: channel for channel in self.antistasi_guild.channels}.get(channel_id)

    async def member_by_name(self, member_name):
        return {member.name.casefold(): member for member in self.antistasi_guild.members}.get(member_name.casefold())

    async def role_from_string(self, role_name):
        return {role.name.casefold(): role for role in self.antistasi_guild.roles}.get(role_name.casefold())

    async def all_members_with_role(self, role: str):
        role = await self.role_from_string(role)
        _out = []
        for member in self.antistasi_guild.members:
            if role in member.roles:
                _out.append(member)
        return list(set(_out))

    async def if_ready(self):
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return AntistasiInformer

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
