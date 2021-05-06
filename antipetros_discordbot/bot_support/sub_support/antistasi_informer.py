"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Dict, Generator, List, Optional, Iterable, Callable, Union, Iterable
import asyncio
import random

from time import time, time_ns, monotonic, monotonic_ns, process_time, process_time_ns, perf_counter, perf_counter_ns
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import discord
from collections import UserDict, namedtuple
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
from antipetros_discordbot.auxiliary_classes.all_item import AllItem
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
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
    everyone_role_id = 449481990513754112
    all_item = AllItem()

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.members_name_dict = None
        self.roles_name_dict = None
        self.channels_name_dict = None

        glog.class_init_notification(log, self)

    @universal_log_profiler
    async def _make_stored_dicts(self):
        if self.antistasi_guild.chunked is False:
            await self.antistasi_guild.chunk(cache=True)
        for cat in ['channels', 'members', 'roles']:
            attr = getattr(self.antistasi_guild, cat)
            name_attr_dict = {item.name.casefold(): item for item in attr}
            setattr(self, f"{cat}_name_dict", name_attr_dict)

    @property
    def everyone_role(self) -> discord.Role:
        return self.get_antistasi_role(self.everyone_role_id)

    @property
    def bertha_emoji(self) -> discord.Emoji:
        return discord.utils.get(self.antistasi_guild.emojis, id=829666475035197470)

    @property
    def antistasi_invite_url(self) -> str:
        return BASE_CONFIG.retrieve('links', 'antistasi_discord_invite', typus=str, direct_fallback='')

    @property
    def armahosts_url(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_url', typus=str, direct_fallback='https://www.armahosts.com/')

    @property
    def armahosts_icon(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_icon', typus=str, direct_fallback='https://pictures.alignable.com/eyJidWNrZXQiOiJhbGlnbmFibGV3ZWItcHJvZHVjdGlvbiIsImtleSI6ImJ1c2luZXNzZXMvbG9nb3Mvb3JpZ2luYWwvNzEwMzQ1MC9BUk1BSE9TVFMtV29ybGRzLUJsdWVJY29uTGFyZ2UucG5nIiwiZWRpdHMiOnsiZXh0cmFjdCI6eyJsZWZ0IjowLCJ0b3AiOjE0Miwid2lkdGgiOjIwNDgsImhlaWdodCI6MjA0OH0sInJlc2l6ZSI6eyJ3aWR0aCI6MTgyLCJoZWlnaHQiOjE4Mn0sImV4dGVuZCI6eyJ0b3AiOjAsImJvdHRvbSI6MCwibGVmdCI6MCwicmlnaHQiOjAsImJhY2tncm91bmQiOnsiciI6MjU1LCJnIjoyNTUsImIiOjI1NSwiYWxwaGEiOjF9fX19')

    @property
    def armahosts_footer_text(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'amahosts_footer_text', typus=str, direct_fallback='We thank ARMAHOSTS for providing the Server')

    @property
    def filesize_limit(self) -> int:
        return self.antistasi_guild.filesize_limit

    @property
    def general_data(self):
        return loadjson(self.general_data_file)

    @ property
    def antistasi_guild(self) -> discord.Guild:
        guild_id = self.bot.get_guild(BASE_CONFIG.retrieve('general_settings', 'guild_id', typus=int, direct_fallback=None))
        if guild_id is None:
            raise ValueError('You need to set "guild_id" under the section "general_settings" in the config file "base_config.ini"')
        return guild_id

    @ property
    def blacklisted_users(self) -> list:
        return loadjson(APPDATA['blacklist.json'])

    async def get_antistasi_emoji(self, name):
        for _emoji in self.antistasi_guild.emojis:
            if _emoji.name.casefold() == name.casefold():
                return _emoji
            await asyncio.sleep(0)

    def blacklisted_user_ids(self) -> Generator[int, None, None]:
        for user_item in self.blacklisted_users:
            yield user_item.get('id')

    async def get_message_directly(self, channel_id: int, message_id: int) -> discord.Message:
        channel = self.channel_from_id(channel_id)
        return await channel.fetch_message(message_id)

    async def fetch_antistasi_member(self, user_id: int) -> discord.Member:
        return await self.antistasi_guild.fetch_member(user_id)

    def channel_from_name(self, channel_name: str) -> discord.abc.GuildChannel:
        if channel_name.casefold() == 'all':
            return self.all_item
        return self.channels_name_dict.get(channel_name.casefold())

    def channel_from_id(self, channel_id: int) -> discord.abc.GuildChannel:
        return self.antistasi_guild.get_channel(channel_id)

    def sync_member_by_id(self, member_id: int) -> discord.Member:
        return self.antistasi_guild.get_member(member_id)

    def member_by_name(self, member_name: str) -> discord.Member:
        if member_name.casefold() == 'all':
            return self.all_item
        return self.members_name_dict.get(member_name.casefold(), None)

    def role_from_string(self, role_name: str) -> discord.Role:
        if role_name.casefold() == 'all':
            return self.all_item
        return self.roles_name_dict.get(role_name.casefold(), None)

    def get_antistasi_role(self, role_id: int) -> discord.Role:
        return self.antistasi_guild.get_role(role_id)

    async def all_members_with_role(self, role: str) -> List[discord.Member]:
        role = await self.role_from_string(role)
        _out = []
        for member in self.antistasi_guild.members:
            if role in member.roles:
                _out.append(member)
        return list(set(_out))

    async def on_ready_setup(self) -> None:
        await self.antistasi_guild.chunk(cache=True)
        await self._make_stored_dicts()
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus) -> None:
        if any(check_typus in typus for check_typus in [UpdateTypus.MEMBERS, UpdateTypus.ROLES, UpdateTypus.GUILD]):
            await self._make_stored_dicts()
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self) -> None:
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class() -> SubSupportBase:
    return AntistasiInformer

# region[Main_Exec]


if __name__ == '__main__':
    # CheckItem = namedtuple("CheckItem", ['name', 'age', 'best_friend'])
    # name_data = loadjson(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\tools\scratches\random_names.json")
    # data = []
    # for name in random.choices(name_data, k=100):
    #     data.append(CheckItem(name, random.randint(1, 100), random.choice(name_data)))
    # st_time = time_ns()
    # x = AutoDict(['name', 'age'], data, True, lambda x: x.casefold(), lambda x: str(x[0]))
    # taken_time = time_ns() - st_time
    # taken_time = taken_time / 1000000000
    # print(taken_time)
    # writejson({key: value._asdict() for key, value in x.items()}, 'checky.json', sort_keys=False)
    pass
# endregion[Main_Exec]
