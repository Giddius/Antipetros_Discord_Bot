"""
Contains custom dynamic invokation prefix implementations.

"""
# region [Imports]

# * Third Party Imports -->
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands import when_mentioned, when_mentioned_or
from typing import Union, List, Tuple, Set, Dict
# * Gid Imports ----------------------------------------------------------------------------------------->
# * Gid Imports -->
import gidlogger as glog
from icecream import ic

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

    config_set_prefixes = BASE_CONFIG.retrieve('prefix', 'command_prefix', typus=List[str], direct_fallback=[])
    all_prefixes = list(set(config_set_prefixes))
    role_exceptions = BASE_CONFIG.retrieve('prefix', 'invoke_by_role_exceptions', typus=List[str], direct_fallback=[])

    def inner(bot, msg):
        extra = [f"{prfx} " for prfx in all_prefixes]
        r = []
        if BASE_CONFIG.retrieve('prefix', 'invoke_by_role_and_mention', typus=bool, direct_fallback=True):
            r = when_mentioned(bot, msg)
            for role in bot.all_bot_roles:
                if role.name not in role_exceptions and role.name.casefold() not in role_exceptions:  # and role.mentionable is True:
                    r += [role.mention + ' ']
        absolutely_all_prefixes = list(set(r + extra))
        return absolutely_all_prefixes

    return inner