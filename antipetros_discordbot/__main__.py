# region [Module_Docstring]

"""
Main module, starts the Antistasi Discord Bot.

"""
# endregion [Module_Docstring]


# region [Imports]
UV_LOOP_IMPORTED = False
# * Standard Library Imports -->
import os
import sys
import platform
import logging
import configparser
import shutil
from pprint import pprint, pformat
import inspect
import asyncio
from datetime import datetime
from contextlib import contextmanager
from time import time, sleep
# * Third Party Imports -->
import discord
from dotenv import load_dotenv
from discord.ext import commands
from watchgod import awatch
if platform.system() == 'Linux':
    try:
        import uvloop
        UV_LOOP_IMPORTED = True
    except ImportError as error:
        print(error)
import click

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.exceptions import TokenError
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.utility.misc import check_if_int
from antipetros_discordbot.utility.gidtools_functions import writejson, writeit, pathmaker, loadjson, readit
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.token_handling import load_tokenfile, store_token_file
from antipetros_discordbot import MAIN_DIR
# endregion[Imports]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
# endregion [Constants]

# region [Logging]

_log_file = glog.log_folderer(__name__, APPDATA)
log_stdout = 'both' if BASE_CONFIG.getboolean('logging', 'log_also_to_stdout') is True else 'file'
log = glog.main_logger(_log_file, BASE_CONFIG.get('logging', 'logging_level'), other_logger_names=['asyncio', 'gidsql', 'gidfiles', "gidappdata"], log_to=log_stdout)
log.info(glog.NEWRUN())
if BASE_CONFIG.getboolean('logging', 'use_logging') is False:
    logging.disable(logging.CRITICAL)
if os.getenv('IS_DEV') == 'yes':
    log.warning('!!!!!!!!!!!!!!!!!IS DEV!!!!!!!!!!!!!!!!!')
# endregion[Logging]


# region [Helper_Functions]


def get_intents():
    if BASE_CONFIG.get('intents', 'convenience_setting') == 'all':
        intents = discord.Intents.all()
    elif BASE_CONFIG.get('intents', 'convenience_setting') == 'default':
        intents = discord.Intents.default()
    else:
        intents = discord.Intents.none()
        for sub_intent in BASE_CONFIG.options('intents'):
            if sub_intent != "convenience_setting":
                setattr(intents, sub_intent, BASE_CONFIG.getboolean('intents', sub_intent))
    return intents


# endregion [Helper_Functions]

# region [Main_function]

@click.group()
def cli():
    pass


@cli.command(name='only_command_info')
def command_info_run():
    anti_petros_bot = AntiPetrosBot(command_prefix='$$', self_bot=False, activity=AntiPetrosBot.activity_from_config(), intents=get_intents())
    _commands = {}
    for cog_name, cog_object in anti_petros_bot.cogs.items():
        for command in cog_object.get_commands():
            clean_params = {}
            for name, parameter in command.clean_params.items():

                clean_params[name] = {'annotation': str(parameter.annotation).replace("<class '", '').replace("'>", '').strip() if parameter.annotation is not parameter.empty else None,
                                      'default': check_if_int(parameter.default) if parameter.default is not parameter.empty else None,
                                      'kind': parameter.kind.description}

            _commands[command.name] = {'cog_name': command.cog_name,
                                       'aliases': command.aliases,
                                       'brief': command.brief,
                                       'clean_params': clean_params,
                                       'description': command.description,
                                       'enabled': command.enabled,
                                       'help': command.help,
                                       'hidden': command.hidden,
                                       'short_doc': command.short_doc,
                                       'signature': command.signature,
                                       'usage': command.usage,
                                       'require_var_positional': command.require_var_positional}
    writejson(_commands, pathmaker(APPDATA['documentation'], 'command_data.json'), sort_keys=True)


@cli.command(name='only_info')
def info_run():
    anti_petros_bot = AntiPetrosBot(command_prefix='$$', self_bot=False, activity=AntiPetrosBot.activity_from_config(), intents=get_intents())


@cli.command(name='stop')
def stop():
    shutdown_trigger_path = pathmaker(APPDATA['shutdown_trigger'], 'shutdown.trigger')
    writeit(shutdown_trigger_path, 'shutdown')
    sleep(10)
    if os.path.isfile(shutdown_trigger_path) is True:
        os.remove(shutdown_trigger_path)
    print(f'AntiPetrosBot was shut down at {datetime.utcnow().strftime("%H:%M:%S on the %Y.%m.%d")}')


@cli.command(name='run')
@click.option('--token_file', '-t', default=None)
@click.option('--save-token-file/--dont-save-token-file', '-save/-nosave', default=False)
def run(token_file, save_token_file):
    main(token_file, save_token_file)


def main(token_file=None, save_token_file=False):
    """
    Starts the Antistasi Discord Bot 'AntiPetros'.

    creates the bot, loads the extensions and starts the bot with the Token.
    """

    if token_file is not None and save_token_file is True:
        store_token_file(token_file)

    token_file = pathmaker(APPDATA["user_env_files"], 'token.env') if token_file is None else pathmaker(token_file)
    with load_tokenfile(token_file):
        discord_token = os.getenv('DISCORD_TOKEN')

    anti_petros_bot = AntiPetrosBot(command_prefix='$$', self_bot=False, activity=AntiPetrosBot.activity_from_config(), intents=get_intents())

    if UV_LOOP_IMPORTED is True:
        uvloop.install()
    try:
        anti_petros_bot.run(discord_token, bot=True, reconnect=True)
    finally:
        discord_token = 'xxxxxxxxxxxxxxxx'


# endregion [Main_function]
# region [Main_Exec]
if __name__ == '__main__':
    if os.getenv('IS_DEV') == 'true':
        main(pathmaker(MAIN_DIR, 'token.env'))
    else:
        main()


# endregion[Main_Exec]
