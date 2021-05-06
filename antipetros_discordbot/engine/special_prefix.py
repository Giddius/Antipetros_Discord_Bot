"""
Contains custom dynamic invokation prefix implementations.

"""
# region [Imports]

# * Third Party Imports -->
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands import when_mentioned, when_mentioned_or
from typing import List
# * Gid Imports ----------------------------------------------------------------------------------------->
# * Gid Imports -->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper


# endregion[Imports]


# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
# endregion[Logging]


def when_mentioned_or_roles_or():
    """
    An alternative to the standard `when_mentioned_or`.

    This makes the bot invocable via:
    * mentioning his name
    * mentioning any of his roles
    * starting a message with any of the entered `prefixes`


    As we need the Bots roles and these can only be gathered after he connected, this function can't be set on instantiation and has to be set on `on_ready`.

    Until then the bots get a simple character as prefix.

    Args:
        prefixes (`Union[str, list]`, optional): Prefixes you want to set extra. Defaults to None.

    Returns:
        `callable`: the dynamic function
    """

    def inner(bot, msg):
        config_set_prefixes = list(set(BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])))
        role_exceptions = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_exceptions', typus=List[str], direct_fallback=[])
        extra = config_set_prefixes
        r = []
        if BASE_CONFIG.retrieve('prefix', 'invoke_by_role_and_mention', typus=bool, direct_fallback=True):
            r.append(bot.user.mention)
            r.append(f"<@!{bot.user.id}>")
            for role in bot.member.roles:
                if role.name.casefold() not in {role_exception.casefold() for role_exception in role_exceptions} and role is not bot.everyone_role:
                    r.append(role.mention + ' ')

        absolutely_all_prefixes = r + extra

        return absolutely_all_prefixes

    return inner
