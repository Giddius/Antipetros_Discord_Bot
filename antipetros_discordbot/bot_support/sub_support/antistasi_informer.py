"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import discord
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
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


class AntistasiInformer(SubSupportBase):
    general_data_file = pathmaker(APPDATA['fixed_data'], 'general_data.json')

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug

        glog.class_init_notification(log, self)

    def check_member_has_any_role(self, role_names: list, member):
        for role_name in role_names:
            if role_name.casefold() in [role.name.casefold() for role in member.roles]:
                return True
        return False

    @property
    def antistasi_invite_url(self):
        return BASE_CONFIG.retrieve('antistasi_info', 'invite_url', typus=str, direct_fallback='')

    @property
    def armahosts_url(self):
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_url', typus=str, direct_fallback='https://www.armahosts.com/')

    @property
    def armahosts_icon(self):
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_icon', typus=str, direct_fallback='https://pictures.alignable.com/eyJidWNrZXQiOiJhbGlnbmFibGV3ZWItcHJvZHVjdGlvbiIsImtleSI6ImJ1c2luZXNzZXMvbG9nb3Mvb3JpZ2luYWwvNzEwMzQ1MC9BUk1BSE9TVFMtV29ybGRzLUJsdWVJY29uTGFyZ2UucG5nIiwiZWRpdHMiOnsiZXh0cmFjdCI6eyJsZWZ0IjowLCJ0b3AiOjE0Miwid2lkdGgiOjIwNDgsImhlaWdodCI6MjA0OH0sInJlc2l6ZSI6eyJ3aWR0aCI6MTgyLCJoZWlnaHQiOjE4Mn0sImV4dGVuZCI6eyJ0b3AiOjAsImJvdHRvbSI6MCwibGVmdCI6MCwicmlnaHQiOjAsImJhY2tncm91bmQiOnsiciI6MjU1LCJnIjoyNTUsImIiOjI1NSwiYWxwaGEiOjF9fX19')

    @property
    def armahosts_footer_text(self):
        return BASE_CONFIG.retrieve('antistasi_info', 'amahosts_footer_text', typus=str, direct_fallback='We thank ARMAHOSTS for providing the Server')

    @property
    def filesize_limit(self):
        return self.antistasi_guild.filesize_limit

    @property
    def dev_members(self):

        return [member for member in self.antistasi_guild.members if self.check_member_has_any_role(["dev helper", "dev team", "dev team lead"], member) is True]

    @property
    def dev_member_by_role(self):
        _out = {"dev team lead": [], "dev team": [], "dev helper": []}
        for member in self.dev_members:
            if member.bot is False:
                if self.check_member_has_any_role(['dev team lead'], member) is True:
                    _out['dev team lead'].append(member)
                elif self.check_member_has_any_role(['dev team'], member) is True:
                    _out['dev team'].append(member)
                elif self.check_member_has_any_role(['dev helper'], member) is True:
                    _out['dev helper'].append(member)
        return _out

    @property
    def general_data(self):
        return loadjson(self.general_data_file)

    @ property
    def antistasi_guild(self):
        return self.bot.get_guild(self.general_data.get('antistasi_guild_id'))

    async def retrieve_antistasi_member(self, user_id):
        return await self.antistasi_guild.fetch_member(user_id)

    def sync_channel_from_name(self, channel_name):
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

    async def channel_from_name(self, channel_name):
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

    def sync_channel_from_id(self, channel_id: int):
        return {channel.id: channel for channel in self.antistasi_guild.channels}.get(channel_id)

    async def channel_from_id(self, channel_id: int):
        return {channel.id: channel for channel in self.antistasi_guild.channels}.get(channel_id)

    def sync_member_by_id(self, member_id: int) -> discord.Member:
        return {member.id: member for member in self.antistasi_guild.members}.get(member_id, None)

    async def member_by_name(self, member_name):
        return {member.name.casefold(): member for member in self.antistasi_guild.members}.get(member_name.casefold(), None)

    async def role_from_string(self, role_name):
        return {role.name.casefold(): role for role in self.antistasi_guild.roles}.get(role_name.casefold())

    async def retrieve_antistasi_role(self, role_id: int):
        return {role.id: role for role in self.antistasi_guild.roles}.get(role_id)

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
