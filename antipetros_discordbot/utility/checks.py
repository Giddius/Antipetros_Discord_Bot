

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import List, Set
import sys
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.exceptions import NotNecessaryRole, IsNotTextChannelError, MissingAttachmentError, NotAllowedChannelError, IsNotDMChannelError, NotNecessaryDmId, NotAllowedMember
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.data import COMMAND_CONFIG_SUFFIXES, DEFAULT_CONFIG_OPTION_NAMES, COG_CHECKER_ATTRIBUTE_NAMES

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]


# endregion[Constants]

class BaseAntiPetrosCheck:

    def __init__(self, checked_types: List = None, allow_creator_skip: bool = False, allow_owner_skip: bool = False):
        self.name = self.__class__.__name__
        self.checked_types = checked_types
        self.allow_creator_skip = allow_creator_skip
        self.allow_owner_skip = allow_owner_skip

    async def __call__(self, ctx: commands.Context):
        bot = ctx.bot
        cog = ctx.cog
        command = ctx.command
        author = ctx.author
        member = await bot.retrieve_antistasi_member(author.id)
        channel = ctx.channel

        if channel.type is discord.ChannelType.private and self.allowed_in_dm(command) is False:
            raise IsNotTextChannelError(ctx, channel.type)
        if self.allow_creator_skip is True and member.id == bot.creator.id:
            log.debug("skipping permission checks as user is creator: %s", ctx.bot.creator.name)
            return True
        if self.allow_owner_skip is True and member.id in bot.owner_ids:
            log.debug("skipping permission checks as user is owner: %s", ctx.author.name)
            return True
        if channel.type is discord.ChannelType.text:
            allowed_channels = self.allowed_channels(command)
            if allowed_channels != {'all'} and channel.name.casefold() not in allowed_channels:
                raise NotAllowedChannelError(ctx, allowed_channels)

        allowed_roles = self.allowed_roles(command)
        if allowed_roles != {'all'} and all(role.name.casefold() not in allowed_roles for role in member.roles):
            raise NotNecessaryRole(ctx, allowed_roles)

        allowed_members = self.allowed_members(command)
        if allowed_members != {'all'} and member not in allowed_members:
            raise NotAllowedMember(allowed_members)
        return True

    def allowed_channels(self, command: commands.Command):
        return {"all"}

    def allowed_roles(self, command: commands.Command):
        return {'all'}

    def allowed_members(self, command: commands.Command):
        return {'all'}

    def allowed_in_dm(self, command: commands.Command):
        return True

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        return self.__class__.__name__


class AllowedChannelAndAllowedRoleCheck(BaseAntiPetrosCheck):
    def __init__(self, in_dm_allowed: bool = False):
        self.in_dm_allowed = in_dm_allowed
        super().__init__(checked_types=["channels", "roles"], allow_creator_skip=True, allow_owner_skip=True)

    def allowed_channels(self, command: commands.Command):
        allowed_channel_names = getattr(command.cog, COG_CHECKER_ATTRIBUTE_NAMES.get('channels'))
        if callable(allowed_channel_names):
            allowed_channel_names = allowed_channel_names(command)
        allowed_channel_names.append('bot-testing')
        return set(map(lambda x: x.casefold(), allowed_channel_names))

    def allowed_roles(self, command: commands.Command):
        allowed_role_names = getattr(command.cog, COG_CHECKER_ATTRIBUTE_NAMES.get('roles'))
        if callable(allowed_role_names):
            allowed_role_names = allowed_role_names(command)
        return set(map(lambda x: x.casefold(), allowed_role_names))

    def allowed_in_dm(self, command: commands.Command):
        return self.in_dm_allowed


class AdminOrAdminLeadCheck(BaseAntiPetrosCheck):
    def __init__(self, in_dm_allowed: bool = False):
        self.in_dm_allowed = in_dm_allowed
        super().__init__(checked_types="roles", allow_creator_skip=True, allow_owner_skip=True)

    def allowed_roles(self, command: commands.Command):
        return {'admin', 'admin lead'}

    def allowed_in_dm(self, command: commands.Command):
        return self.in_dm_allowed


class OnlyBobMurphyCheck(BaseAntiPetrosCheck):
    def __init__(self):
        super().__init__(checked_types=['members'])

    def allowed_members(self, command: commands.Command):
        bot = command.cog.bot
        bob_murphy_member = bot.sync_member_by_id(346595708180103170)
        return {bob_murphy_member}


class OnlyGiddiCheck(BaseAntiPetrosCheck):
    def __init__(self):
        super().__init__(checked_types=['members'])

    def allowed_members(self, command: commands.Command):
        bot = command.cog.bot
        giddi_member = bot.sync_member_by_id(576522029470056450)
        return {giddi_member}


class HasAttachmentCheck(BaseAntiPetrosCheck):
    def __init__(self, min_amount_attachments: int = 1):
        self.min_amount_attachments = min_amount_attachments
        super().__init__(checked_types=['attachment'])

    async def __call__(self, ctx: commands.Context):
        if super().__call__(ctx) is True:
            if len(ctx.message.attachments) < self.min_amount_attachments:
                raise MissingAttachmentError(ctx, self.min_amount_attachments)
            return True


def in_allowed_channels():
    def predicate(ctx: commands.Context):
        cog = ctx.cog
        command = ctx.command
        author = ctx.author
        channel = ctx.channel
        bot = ctx.bot
        if channel.type is discord.ChannelType.private:
            raise IsNotTextChannelError(ctx, channel.type)
        allowed_channel_names = getattr(cog, COG_CHECKER_ATTRIBUTE_NAMES.get('channels'))
        if callable(allowed_channel_names):
            allowed_channel_names = allowed_channel_names(command)
        if allowed_channel_names != ['all'] and channel.name.casefold() not in allowed_channel_names + ['bot-testing']:
            raise NotAllowedChannelError(ctx, allowed_channel_names)
        return True
    predicate.check_name = sys._getframe().f_code.co_name
    return commands.check(predicate)


def log_invoker(logger, level: str = 'info'):
    # TODO: make as before invoke hook and not check!
    def predicate(ctx):
        channel_name = ctx.channel.name if ctx.channel.type is discord.ChannelType.text else 'DM'
        getattr(logger, level)("command '%s' as '%s' -- invoked by: name: '%s', id: %s -- in channel: '%s' -- raw invoking message: '%s'",
                               ctx.command.name, ctx.invoked_with, ctx.author.name, ctx.author.id, channel_name, ctx.message.content)

        return True
    predicate.check_name = sys._getframe().f_code.co_name
    return commands.check(predicate)


def purge_check_from_user(user_id: int):

    def is_from_user(message):
        return message.author.id == user_id
    return is_from_user


def purge_check_contains(word: str, case_sensitive=False):
    def contains_in_content(message):
        content = message.content
        check_word = word
        if case_sensitive is False:
            content = message.content.casefold()
            check_word = word.casefold()
        return check_word in content.split()
    return contains_in_content


def purge_check_is_bot():
    def message_is_from_bot(message):
        return message.author.bot
    return message_is_from_bot


def purge_check_always_true():
    def always_true(message):
        return True
    return always_true


def purge_check_always_false():
    def always_false(message):
        return False
    return always_false


PURGE_CHECK_TABLE = {'is_bot': purge_check_is_bot,
                     'contains': purge_check_contains,
                     'from_user': purge_check_from_user,
                     'all': purge_check_always_true}


def has_attachments(min_amount_attachments: int = 1):
    return commands.check(HasAttachmentCheck(min_amount_attachments))


def is_not_giddi(ctx: commands.Context):
    if ctx.author.id == ctx.bot.creator.id:
        return False
    return True


def only_dm_only_allowed_id(config_name: str, allowed_id_key: str = "allowed_in_dms"):
    async def predicate(ctx):
        user_id = ctx.author.id
        channel_type = ctx.channel.type
        if channel_type is not discord.ChannelType.private:
            raise IsNotDMChannelError(ctx, channel_type)
        if user_id not in set(map(int, COGS_CONFIG.getlist(config_name, allowed_id_key))):
            return False
        return True
    predicate.check_name = sys._getframe().f_code.co_name
    return commands.check(predicate)


def allowed_channel_and_allowed_role(in_dm_allowed: bool = False):

    return commands.check(AllowedChannelAndAllowedRoleCheck(in_dm_allowed=in_dm_allowed))


def mod_func_all_in_int(x):
    if x.casefold() == 'all':
        return x.casefold()
    return int(x)


def dynamic_enabled_checker(command: commands.Command, fall_back: bool = True):
    option_name = command.name + COMMAND_CONFIG_SUFFIXES.get('enabled')[0]
    config_name = command.cog.config_name
    return COGS_CONFIG.retrieve(config_name, option_name, typus=bool, direct_fallback=fall_back)


def command_enabled_checker(config_name: str):

    def _check_command_enabled(command_name: str):
        option_name = command_name + COMMAND_CONFIG_SUFFIXES.get('enabled')[0]
        return COGS_CONFIG.retrieve(config_name, option_name, typus=bool, direct_fallback=True)

    return _check_command_enabled


def allowed_requester(cog, data_type: str):
    cog_section_name = cog.config_name
    if data_type not in COMMAND_CONFIG_SUFFIXES:
        raise TypeError(f"data_type '{data_type}' is not an valid option")

    def _allowed_data(command):

        command_name = command if isinstance(command, str) else command.name

        option_name = command_name + COMMAND_CONFIG_SUFFIXES.get(data_type)[0].replace(' ', '_')
        fallback_option = DEFAULT_CONFIG_OPTION_NAMES.get(data_type)
        if data_type == 'dm_ids':
            return COGS_CONFIG.retrieve(cog_section_name, option_name, typus=Set[str], fallback_option=fallback_option, mod_func=mod_func_all_in_int)
        return COGS_CONFIG.retrieve(cog_section_name, option_name, typus=List[str], fallback_option=fallback_option, mod_func=lambda x: x.casefold())

    return _allowed_data


def owner_or_admin(allowed_in_dm: bool = False):

    return commands.check(AdminOrAdminLeadCheck(in_dm_allowed=allowed_in_dm))


def only_giddi():

    return commands.check(OnlyGiddiCheck())


def only_bob():

    return commands.check(OnlyBobMurphyCheck())


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
