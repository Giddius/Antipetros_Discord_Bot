# region [Module_Docstring]

"""
Main module, starts the Antistasi Discord Bot.

"""
# endregion [Module_Docstring]


# region [Imports]

# * Standard Library Imports -->
import os
import sys
import logging
import configparser
from pprint import pprint, pformat
import inspect
import asyncio
# * Third Party Imports -->
import discord
from dotenv import load_dotenv
from discord.ext import commands
from watchgod import awatch
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.exceptions import TokenError
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

from antipetros_discordbot.utility.gidtools_functions import writejson

# endregion[Imports]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')

# endregion [Constants]

# region [Logging]

_log_file = glog.log_folderer(__name__, APPDATA)
log = glog.main_logger(_log_file, BASE_CONFIG.get('logging', 'logging_level'), other_logger_names=['asyncio', 'gidsql', 'gidfiles'])
log.info(glog.NEWRUN())
if BASE_CONFIG.getboolean('logging', 'use_logging') is False:
    logging.disable(logging.CRITICAL)

# endregion[Logging]


# region [Helper_Functions]


def get_token():
    """
    Reloads env file then reads and returns the Token.

    Args:
        envfile (str, optional): path to env file. Defaults to None.

    Raises:
        TokenError: raised if Token is not set in the env or set to nothing or set to 'xxxx'

    Returns:
        str: Token
    """

    load_dotenv(APPDATA['.env'])
    _temp_token = os.getenv('DISCORD_TOKEN')
    if _temp_token not in [None, '', 'xxxx']:
        return _temp_token
    else:
        raise TokenError('token loaded from enviroment is empty or not set')


# endregion [Helper_Functions]

# region [Main_function]


async def debug_function(bot):
    log.debug("debug function triggered")
    log.warning('nothing set in debug function for "%s"', bot.user.name)


def main():
    """
    Starts the Antistasi Discord Bot 'AntiPetros'.

    creates the bot, loads the extensions and starts the bot with the Token.
    """

    ANTI_PETROS_BOT = AntiPetrosBot(command_prefix='$$', self_bot=False, activity=AntiPetrosBot.activity_from_config())

    @ANTI_PETROS_BOT.event
    async def on_ready():
        log.info('%s has connected to Discord!', ANTI_PETROS_BOT.user.name)

        channel = ANTI_PETROS_BOT.get_channel(BASE_CONFIG.getint('startup_message', 'channel'))
        if ANTI_PETROS_BOT.startup_message is not None:
            delete_time = 15 if ANTI_PETROS_BOT.is_debug is True else 60
            await ANTI_PETROS_BOT.get_channel(ANTI_PETROS_BOT.startup_message[0]).send(ANTI_PETROS_BOT.startup_message[1], delete_after=delete_time)
        await asyncio.sleep(5)
        if ANTI_PETROS_BOT.is_debug:
            await debug_function(ANTI_PETROS_BOT)

    if len(sys.argv) == 1 or sys.argv[1] != 'get_info_run':
        log.info('trying to log on as %s!', str(ANTI_PETROS_BOT))
        ANTI_PETROS_BOT.run(get_token(), bot=True, reconnect=True)


# endregion [Main_function]
if __name__ == '__main__':
    main()
