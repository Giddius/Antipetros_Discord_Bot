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


class AutoDict(UserDict):

    def __init__(self, key_attribute: Union[str, Iterable[str]], items: Optional[Iterable] = None, keep_sorted: bool = False, key_modifier: Callable = None, sort_key: Callable = None) -> None:
        self._key_attribute = key_attribute if isinstance(key_attribute, (list, set, tuple, frozenset)) else [key_attribute]
        self.key_modifier = key_modifier
        self.is_multi = len(self.key_attribute) > 1
        self._keep_sorted = keep_sorted
        self._sort_key = sort_key
        self._reverse = False
        super().__init__()
        if items is not None:
            self.add_items(items)

    def _try_key_modifier(self, in_data):
        try:
            return self.key_modifier(in_data)
        except AttributeError:
            return in_data

    def _update(self):
        items = list(self.data.values())
        self.data = {}
        self.add_items(items)

    def add_items(self, items: Iterable):
        for item in items:
            for attr in self.key_attribute:
                key = getattr(item, attr)
                if self.key_modifier is not None:
                    key = self._try_key_modifier(key)
                self.data[key] = item
        self.sort()

    def get(self, key, default=None):
        key = self._try_key_modifier(key)
        return self.data.get(key, default)

    def __setitem__(self, key, item):
        if self.key_modifier is not None:
            key = self._try_key_modifier(key)
        super().__setitem__(key=key, item=item)

    def __contains__(self, key):
        try:
            return self._try_key_modifier(getattr(key, self.key_attribute)) in self.data.values()
        except AttributeError:
            pass

        key = self._try_key_modifier(key)

        return super().__contains__(key=key)

    def __getitem__(self, key):
        key = self._try_key_modifier(key)
        return super().__getitem__(key=key)

    def __delitem__(self, key):
        key = self._try_key_modifier(key)
        super().__delitem__(key=key)

    def sort(self):
        if self.keep_sorted is True:
            self.data = dict(sorted(self.data.items(), key=self.sort_key, reverse=self.reverse))

    @property
    def key_attribute(self):
        return self._key_attribute

    @key_attribute.setter
    def key_attribute(self, value):
        if value != self._key_attribute:
            self._key_attribute = value if isinstance(value, (list, set, tuple, frozenset)) else [value]
            self._update()

    @property
    def keep_sorted(self):
        return self._keep_sorted

    @keep_sorted.setter
    def keep_sorted(self, value):
        if isinstance(value, bool) is False:
            raise TypeError("keep_sorted needs to be of type bool")
        if value is not self._keep_sorted:
            self._keep_sorted = value
            self.sort()

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, value):
        if not callable(value):
            raise TypeError('sort_key needs to be an callable')
        self._sort_key = value
        self.sort()

    @property
    def reverse(self):
        return self._reverse

    @reverse.setter
    def reverse(self, value):
        if not isinstance(value, bool):
            raise TypeError('reverse needs to of type bool')
        if value is not self._reverse:
            self._reverse = value
            self.sort()

    @classmethod
    def fromkeys(cls, iterable, value=None):
        return NotImplemented


class AntistasiInformer(SubSupportBase):
    general_data_file = pathmaker(APPDATA['fixed_data'], 'general_data.json')
    everyone_role_id = 449481990513754112
    all_item = AllItem()

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.members_dict = None
        self.roles_dict = None
        self.channels_dict = None

        glog.class_init_notification(log, self)

    def check_member_has_any_role(self, role_names: List[str], member: discord.Member) -> bool:
        for role_name in role_names:
            if role_name.casefold() in [role.name.casefold() for role in member.roles]:
                return True
        return False

    @universal_log_profiler
    async def _make_stored_dicts(self):
        for cat in ['channels', 'members', 'roles']:
            attr = getattr(self.antistasi_guild, cat)

            setattr(self, f"{cat}_dict", AutoDict(['name', 'id'], attr, keep_sorted=True, key_modifier=lambda x: x.lower(), sort_key=lambda x: x[1].created_at))

    @property
    def everyone_role(self) -> discord.Role:
        return self.sync_retrieve_antistasi_role(self.everyone_role_id)

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
    def dev_members(self) -> List[discord.Member]:

        return [member for member in self.antistasi_guild.members if self.check_member_has_any_role(["dev helper", "dev team", "dev team lead"], member) is True]

    @property
    def dev_member_by_role(self) -> Dict[str, List[discord.Member]]:
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
    def antistasi_guild(self) -> discord.Guild:
        guild_id = self.bot.get_guild(BASE_CONFIG.retrieve('general_settings', 'guild_id', typus=int, direct_fallback=None))
        if guild_id is None:
            raise ValueError('You need to set "guild_id" under the section "general_settings" in the config file "base_config.ini"')
        return guild_id

    @ property
    def blacklisted_users(self) -> list:
        return loadjson(APPDATA['blacklist.json'])

    def blacklisted_user_ids(self) -> Generator[int, None, None]:
        for user_item in self.blacklisted_users:
            yield user_item.get('id')

    async def get_message_directly(self, channel_id: int, message_id: int) -> discord.Message:
        channel = await self.channel_from_id(channel_id)
        return await channel.fetch_message(message_id)

    async def retrieve_antistasi_member(self, user_id: int) -> discord.Member:
        return await self.antistasi_guild.fetch_member(user_id)

    def sync_channel_from_name(self, channel_name: str) -> discord.abc.GuildChannel:
        if channel_name.casefold() == 'all':
            return self.all_item
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

    async def channel_from_name(self, channel_name: str) -> discord.abc.GuildChannel:
        if channel_name.casefold() == 'all':
            return self.all_item
        return {channel.name.casefold(): channel for channel in self.antistasi_guild.channels}.get(channel_name.casefold())

    def sync_channel_from_id(self, channel_id: int) -> discord.abc.GuildChannel:
        return {channel.id: channel for channel in self.antistasi_guild.channels}.get(channel_id)

    async def channel_from_id(self, channel_id: int) -> discord.abc.GuildChannel:
        return {channel.id: channel for channel in self.antistasi_guild.channels}.get(channel_id)

    def sync_member_by_id(self, member_id: int) -> discord.Member:
        return self.members_dict.get(member_id, None)

    def sync_member_by_name(self, member_name: str) -> discord.Member:
        if member_name.casefold() == 'all':
            return self.all_item
        return self.members_dict.get(member_name.casefold(), None)

    async def member_by_name(self, member_name: str) -> discord.Member:
        if member_name.casefold() == 'all':
            return self.all_item
        return self.members_dict.get(member_name.casefold(), None)

    def sync_role_from_string(self, role_name: str) -> discord.Role:
        if role_name.casefold() == 'all':
            return self.all_item
        return self.roles_dict.get(role_name.casefold(), None)

    async def role_from_string(self, role_name) -> discord.Role:
        if role_name.casefold() == 'all':
            return self.all_item
        return self.roles_dict.get(role_name.casefold())

    async def retrieve_antistasi_role(self, role_id: int) -> discord.Role:
        return {role.id: role for role in self.antistasi_guild.roles}.get(role_id)

    def sync_retrieve_antistasi_role(self, role_id: int) -> discord.Role:
        return {role.id: role for role in self.antistasi_guild.roles}.get(role_id)

    async def all_members_with_role(self, role: str) -> List[discord.Member]:
        role = await self.role_from_string(role)
        _out = []
        for member in self.antistasi_guild.members:
            if role in member.roles:
                _out.append(member)
        return list(set(_out))

    async def if_ready(self) -> None:
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
