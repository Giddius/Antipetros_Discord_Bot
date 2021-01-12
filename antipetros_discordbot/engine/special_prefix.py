from discord.ext.commands import when_mentioned
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
import gidlogger as glog
# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

BASE_CONFIG = SupportKeeper.get_config('base_config')
# endregion[Logging]


def when_mentioned_or_roles_or(prefixes=None):

    prefixes = BASE_CONFIG.get('prefix', 'command_prefix') if prefixes is None else prefixes
    role_exceptions = BASE_CONFIG.getlist('prefix', 'invoke_by_role_exceptions')

    def inner(bot, msg):

        extra = list(prefixes)
        r = when_mentioned(bot, msg)
        for role in bot.all_bot_roles:
            if role.name not in role_exceptions and role.name.casefold() not in role_exceptions:  # and role.mentionable is True:
                r += [role.mention + ' ']
        return r + extra

    return inner
