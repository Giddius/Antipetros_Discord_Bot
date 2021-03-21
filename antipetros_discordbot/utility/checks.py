

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import List, Set
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext import commands

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.exceptions import NotNecessaryRole, IsNotTextChannelError, MissingAttachmentError, NotAllowedChannelError, IsNotDMChannelError, NotNecessaryDmId
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
    return commands.check(predicate)


def log_invoker(logger, level: str = 'info'):
    def predicate(ctx):
        channel_name = ctx.channel.name if ctx.channel.type is discord.ChannelType.text else 'DM'
        getattr(logger, level)("command '%s' as '%s' -- invoked by: name: '%s', id: %s -- in channel: '%s' -- raw invoking message: '%s'",
                               ctx.command.name, ctx.invoked_with, ctx.author.name, ctx.author.id, channel_name, ctx.message.content)

        return True
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
    def predicate(ctx):
        if len(ctx.message.attachments) >= min_amount_attachments:
            return True
        else:
            raise MissingAttachmentError(ctx, min_amount_attachments)

    return commands.check(predicate)


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

    return commands.check(predicate)


def allowed_channel_and_allowed_role_2(in_dm_allowed: bool = False):
    async def predicate(ctx: commands.Context):
        cog = ctx.cog
        command = ctx.command
        author = ctx.author
        channel = ctx.channel
        bot = ctx.bot
        log.debug("in_dm_allowed for '%s': %s", command.name, str(in_dm_allowed))
        if channel.type is discord.ChannelType.private:
            if in_dm_allowed is False:
                raise IsNotTextChannelError(ctx, channel.type)

            if await bot.is_owner(author):
                log.debug("skipping permission check as user is creator/owner: %s", ctx.author.name)
                return True

            allowed_dm_ids = getattr(cog, COG_CHECKER_ATTRIBUTE_NAMES.get('dm_ids'))
            if callable(allowed_dm_ids):
                allowed_dm_ids = allowed_dm_ids(command)
            log.debug("allowed_dm_ids for '%s': %s", command.name, str(allowed_dm_ids))
            if allowed_dm_ids != ["all"] and author.id not in allowed_dm_ids:
                raise NotNecessaryDmId(ctx)
        else:
            allowed_channel_names = getattr(cog, COG_CHECKER_ATTRIBUTE_NAMES.get('channels'))
            if callable(allowed_channel_names):
                allowed_channel_names = allowed_channel_names(command)
            allowed_channel_names = allowed_channel_names + ['bot-testing']
            log.debug("allowed_channel_names for '%s': %s", command.name, str(allowed_channel_names))
            if allowed_channel_names != ['all'] and channel.name.casefold() not in allowed_channel_names:
                raise NotAllowedChannelError(ctx, allowed_channel_names)

            if await bot.is_owner(author):
                log.debug("skipping permission check as user is creator/owner: %s", ctx.bot.creator.name)
                return True

            allowed_role_names = getattr(cog, COG_CHECKER_ATTRIBUTE_NAMES.get('roles'))
            if callable(allowed_role_names):
                allowed_role_names = allowed_role_names(command)
            log.debug("allowed_role_names for '%s': %s", command.name, str(allowed_role_names))
            if allowed_role_names != ['all'] and all(role.name.casefold() not in allowed_role_names for role in author.roles):
                raise NotNecessaryRole(ctx, allowed_role_names)

        return True

    return commands.check(predicate)


def mod_func_all_in_int(x):
    if x.casefold() == 'all':
        return x.casefold()
    return int(x)


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


def owner_or_admin(allowe_in_dm: bool = False):
    async def predicate(ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.channel.type is discord.ChannelType.text:
            if 'admin' in {role.name.casefold() for role in ctx.author.roles}:
                return True
        elif ctx.channel.type is discord.ChannelType.private and allowe_in_dm is True:
            member = ctx.bot.sync_member_by_id(ctx.author.id)
            if 'admin' in {role.name.casefold() for role in member.roles}:
                return True

        return False
    return commands.check(predicate)


def only_giddi():
    async def predicate(ctx: commands.Context):
        if ctx.author.id == ctx.bot.creator.id:
            return True
        return False
    return commands.check(predicate)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]