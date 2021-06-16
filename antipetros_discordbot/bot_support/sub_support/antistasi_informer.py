"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Generator, List, Union
import asyncio

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import discord
from sortedcontainers import SortedDict, SortedList
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
from functools import cached_property
from antipetros_discordbot.auxiliary_classes.all_item import AllItem
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
    color_emoji_id_map = {'default': 839782169303449640,
                          'black': 844965636861067295,
                          'blue': 844965636585422889,
                          'brown': 844965636811784192,
                          'cyan': 844965636711251979,
                          'dark_orange': 845066731545952266,
                          'firebrick': 845066731327979522,
                          'gold': 845066731558928384,
                          'gray': 844965636920442890,
                          'green': 844965636920573953,
                          'honeydew': 845066731550277652,
                          'light_blue': 845066731567185970,
                          'olive': 844965636944691221,
                          'orange': 844965636911530074,
                          'pink': 844965636849008660,
                          'purple': 844965636895014963,
                          'red': 844965637058461696,
                          'tan': 845066731562205244,
                          'violet': 844965636895277097,
                          'white': 844965636958715914,
                          'yellow': 844965637160042496,
                          'yellowgreen': 845066731624857610}

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.members_name_dict = None
        self.roles_name_dict = None
        self.channels_name_dict = None
        self.antistasi_guild_id = self.get_antistasi_guild_id()
        self._antistasi_guild = None

        glog.class_init_notification(log, self)

    async def _make_stored_dicts(self):
        if self.antistasi_guild.chunked is False:
            await self.antistasi_guild.chunk(cache=True)
        for cat in ['channels', 'members', 'roles']:
            attr = getattr(self.antistasi_guild, cat)
            name_attr_dict = {item.name.casefold(): item for item in attr}
            setattr(self, f"{cat}_name_dict", name_attr_dict)
            log.info("created '%s_name_dict' fresh", cat)

    @cached_property
    def everyone_role(self) -> discord.Role:
        return self.get_antistasi_role(self.everyone_role_id)

    @cached_property
    def antistasi_image(self):
        return "https://avatars0.githubusercontent.com/u/53788409?s=200&v=4"

    @cached_property
    def salute_emoji(self):
        return discord.utils.get(self.antistasi_guild.emojis, id=755173152752926753)

    @cached_property
    def bertha_emoji(self) -> discord.Emoji:
        return discord.utils.get(self.antistasi_guild.emojis, id=829666475035197470)

    @cached_property
    def bot_emoji(self) -> discord.Emoji:
        return discord.utils.get(self.bot_testing_guild.emojis, id=839782169303449640)

    @cached_property
    def server_emoji(self) -> discord.Emoji:
        return discord.utils.get(self.bot_testing_guild.emojis, id=845740762900856838)

    @cached_property
    def antistasi_invite_url(self) -> str:
        return BASE_CONFIG.retrieve('links', 'antistasi_discord_invite', typus=str, direct_fallback='')

    @cached_property
    def armahosts_url(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_url', typus=str, direct_fallback='https://www.armahosts.com/game')

    @cached_property
    def armahosts_icon(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'armahosts_icon', typus=str, direct_fallback='https://pictures.alignable.com/eyJidWNrZXQiOiJhbGlnbmFibGV3ZWItcHJvZHVjdGlvbiIsImtleSI6ImJ1c2luZXNzZXMvbG9nb3Mvb3JpZ2luYWwvNzEwMzQ1MC9BUk1BSE9TVFMtV29ybGRzLUJsdWVJY29uTGFyZ2UucG5nIiwiZWRpdHMiOnsiZXh0cmFjdCI6eyJsZWZ0IjowLCJ0b3AiOjE0Miwid2lkdGgiOjIwNDgsImhlaWdodCI6MjA0OH0sInJlc2l6ZSI6eyJ3aWR0aCI6MTgyLCJoZWlnaHQiOjE4Mn0sImV4dGVuZCI6eyJ0b3AiOjAsImJvdHRvbSI6MCwibGVmdCI6MCwicmlnaHQiOjAsImJhY2tncm91bmQiOnsiciI6MjU1LCJnIjoyNTUsImIiOjI1NSwiYWxwaGEiOjF9fX19')

    @cached_property
    def armahosts_emoji(self):
        return discord.utils.get(self.antistasi_guild.emojis, id=839468368402317353)

    @cached_property
    def armahosts_footer_text(self) -> str:
        return BASE_CONFIG.retrieve('antistasi_info', 'amahosts_footer_text', typus=str, direct_fallback='We thank ARMAHOSTS for providing the Server')

    @property
    def filesize_limit(self) -> int:
        return self.antistasi_guild.filesize_limit

    @property
    def general_data(self):
        return loadjson(self.general_data_file)

    def get_antistasi_guild_id(self):
        _out = BASE_CONFIG.retrieve('general_settings', 'guild_id', typus=int, direct_fallback=None)
        if _out is None:
            raise ValueError('You need to set "guild_id" under the section "general_settings" in the config file "base_config.ini"')
        return _out

    @property
    def antistasi_guild(self) -> discord.Guild:
        if self._antistasi_guild is None:
            self._antistasi_guild = self.bot.get_guild(self.antistasi_guild_id)
        return self._antistasi_guild

    @cached_property
    def bot_testing_guild(self) -> discord.Guild:
        guild = self.bot.get_guild(837389179025096764)
        return guild

    @ property
    def blacklisted_users(self) -> list:
        return loadjson(APPDATA['blacklist.json'])

    async def get_color_emoji(self, color_name: str):
        color_emoji_id = self.color_emoji_id_map.get(color_name.casefold(), 839782169303449640)
        return discord.utils.get(self.bot_testing_guild.emojis, id=color_emoji_id)

    async def get_antistasi_emoji(self, name):
        for _emoji in self.antistasi_guild.emojis:
            if _emoji.name.casefold() == name.casefold():
                return _emoji
            await asyncio.sleep(0)

    def blacklisted_user_ids(self) -> Generator[int, None, None]:
        for user_item in self.blacklisted_users:
            yield user_item.get('id')

    async def ensure_dm_channel(self, target: Union[discord.Member, discord.User]) -> discord.DMChannel:
        _out = target.dm_channel
        if _out is None:
            _out = await target.create_dm()
        return _out

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

    def get_antistasi_member(self, member_id: int) -> discord.Member:
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

    def get_channel_link(self, channel: Union[int, str, discord.TextChannel]):
        base_url = "https://discord.com/channels"
        if isinstance(channel, discord.TextChannel):
            channel_id = channel.id
        elif isinstance(channel, str):
            channel_id = self.channel_from_name(channel).id
        elif isinstance(channel, int):
            channel_id = channel

        return f"{base_url}/{self.antistasi_guild_id}/{channel_id}"

    def get_message_link(self, channel: Union[int, str, discord.TextChannel], message_id: int):
        return self.get_channel_link(channel) + f"/{message_id}"

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
        if any(check_typus in typus for check_typus in [UpdateTypus.MEMBERS, UpdateTypus.ROLES, UpdateTypus.GUILD, UpdateTypus.RECONNECT, UpdateTypus.CYCLIC]):
            self._antistasi_guild = None
            await self._make_stored_dicts()
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self) -> None:
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class() -> SubSupportBase:
    return AntistasiInformer

# region[Main_Exec]


if __name__ == '__main__':
    pass
# endregion[Main_Exec]
