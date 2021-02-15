# region [Module_Docstring]

"""
Main module, starts the Antistasi Discord Bot.
On the Cli use: antipetrosbot run [-t token file] [-save]

"""
# endregion [Module_Docstring]


# region [Imports]

import os
import logging
from time import sleep
from datetime import datetime
import click
import discord
from dotenv import find_dotenv, load_dotenv
import gidlogger as glog
from antipetros_discordbot import MAIN_DIR
from antipetros_discordbot.utility.misc import check_if_int, generate_base_cogs_config, save_commands, generate_help_data
from antipetros_discordbot.utility.crypt import decrypt_db, encrypt_db
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.utility.gidtools_functions import writeit, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

# endregion[Imports]

# region [TODO]


# endregion [TODO]


# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
COGS_CONFIG.save()
# endregion [Constants]

# region [Logging]


def configure_logger():
    """
    Configures the logger from the base_config.ini file.
    When logging to file, the file rotates every new run and also when it reaches a size of 10mb.
    Mainly to either log to stdout and a file or only a file and how many files it should keep.
    """
    # TODO: way to convoluted, make it simpler look into better loggign frameworks.

    def from_config(key, attr_name):
        """
        Helper func to get values from the config, without having to type the section repetedly.

        Args:
            key (str): option name in the config
            attr_name (str): attribute to use to retrieve the value, i.e.: getboolean, get, getint

        Returns:
            [Any]: the desired value with, type is dictated by the attribute that is used to retrieve it (attr_name)
        """

        return getattr(BASE_CONFIG, attr_name)('logging', key)
    log_stdout = 'both' if from_config('log_also_to_stdout', 'getboolean') is True else 'file'
    log_level = from_config('logging_level', 'get')
    _log_file = glog.log_folderer(__name__, APPDATA)
    in_back_up = from_config('amount_keep_old_logs', 'getint')
    use_logging = from_config('use_logging', 'getboolean')
    if os.getenv('IS_DEV') == 'true':
        log_stdout = 'both'

    _log = glog.main_logger(_log_file, log_level, other_logger_names=['asyncio', 'gidsql', 'gidfiles', "gidappdata"], log_to=log_stdout, in_back_up=in_back_up)
    # _log.info(glog.NEWRUN())
    if use_logging is False:
        logging.disable(logging.CRITICAL)
    if os.getenv('IS_DEV') == 'yes':
        _log.warning('!!!!!!!!!!!!!!!!!!! IS DEV !!!!!!!!!!!!!!!!!!!')
        _log.warning('!!!!!!!!!!!!!!!!! DEBUG MODE !!!!!!!!!!!!!!!!!')
    return _log


log = configure_logger()
# endregion[Logging]


# region [Helper]


# endregion [Helper]

# region [Main_function]

@click.group()
def cli():
    """
    dummy function to initiate click group.

    """


@cli.group()
def collect_data():
    """
    dummy function to initiate click group.

    """


@collect_data.command(name='command')
@click.option('--output-file', '-o', default=None)
@click.option('--verbose', '-v', type=bool, default=False)
def command_info_run(output_file, verbose):
    """
    Function and cli command to start up the bot, collect bot-commands extended info, but not connect to discord.

    collected as json in /docs

    """
    if verbose is False:
        logging.disable(logging.CRITICAL)
    anti_petros_bot = AntiPetrosBot()
    for cog_name, cog_object in anti_petros_bot.cogs.items():
        print(f"Collecting command-info for '{cog_name}'")
        save_commands(cog_object, output_file=output_file)
    print('#' * 15 + ' finished collecting command-infos ' + '#' * 15)


@collect_data.command(name='config')
@click.option('--output-file', '-o', default=None)
@click.option('--verbose', '-v', type=bool, default=False)
def config_data_run(output_file, verbose):
    if verbose is False:
        logging.disable(logging.CRITICAL)
    anti_petros_bot = AntiPetrosBot()
    print("Generating Prototype cogs_config.ini")
    generate_base_cogs_config(anti_petros_bot, output_file=output_file)
    print('#' * 15 + ' finished generating Prototype cogs_config.ini ' + '#' * 15)


@collect_data.command(name='bot-help')
@click.option('--output-file', '-o', default=None)
@click.option('--verbose', '-v', type=bool, default=False)
def bot_help_data_run(output_file, verbose):
    if verbose is False:
        logging.disable(logging.CRITICAL)
    anti_petros_bot = AntiPetrosBot()
    for cog_name, cog_object in anti_petros_bot.cogs.items():
        print(f"Collecting help-data for '{cog_name}'")
        generate_help_data(cog_object, output_file=output_file)
    print('#' * 15 + ' finished collecting help-data ' + '#' * 15)


def non_click_command_info_run():
    """
    Function and cli command to start up the bot, collect bot-commands extended info, but not connect to discord.

    collected as json in /docs

    """
    anti_petros_bot = AntiPetrosBot()
    generate_base_cogs_config(anti_petros_bot)
    command_json_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/commands.json')
    command_help_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/command_help.json')
    for file in [command_json_file, command_help_file]:
        if os.path.isfile(file) is True:
            os.remove(file)
    for cog_name, cog_object in anti_petros_bot.cogs.items():
        save_commands(cog_object)


@cli.command(name="clean")
def clean_user_data():
    if os.environ['IS_DEV'].casefold() in ['true', 'yes', '1'] or APPDATA.dev is True:
        raise RuntimeError("Cleaning not possible in Dev Mode")
    APPDATA.clean(APPDATA.AllFolder)


@cli.command(name='stop')
def stop():
    """
    Cli way of autostoping the bot.
    creates and file in a specific folder that acts like a shutdown trigger (bot watches the folder)
    afterwards deletes the file. Used as redundant way to shut down if other methods fail, if this fails, the server has to be restarted.

    """
    shutdown_trigger_path = pathmaker(APPDATA['shutdown_trigger'], 'shutdown.trigger')
    writeit(shutdown_trigger_path, 'shutdown')
    sleep(10)
    if os.path.isfile(shutdown_trigger_path) is True:
        os.remove(shutdown_trigger_path)
    print(f'AntiPetrosBot was shut down at {datetime.utcnow().strftime("%H:%M:%S on the %Y.%m.%d")}')


@cli.command(name='run')
@click.option('--token', '-t')
@click.option('--steam-api-key', '-s')
def run(token):
    """
    Standard way to start the bot and connect it to discord.
    takes the token as string and the key to decrypt the db also as string.
    calls the actual main() function.

    Args:
        token_file ([str]): discord token
        save_token_file ([str]): key to decrypt the db's
    """
    os.environ['INFO_RUN'] = "0"
    main(token=token)


def main(token: str):
    """
    Starts the Antistasi Discord Bot 'AntiPetros'.

    creates the bot, loads the extensions and starts the bot with the Token.
    is extra function so the bot can be started via cli but also from within vscode.

    Args:
        token_file ([str]): discord token
        save_token_file ([str]): key to decrypt the db's
    """
    os.environ['INFO_RUN'] = "0"
    anti_petros_bot = AntiPetrosBot(token=token)

    anti_petros_bot.run()


# endregion [Main_function]
# region [Main_Exec]
if __name__ == '__main__':
    if os.getenv('IS_DEV') == 'true':
        load_dotenv('token.env')

        main(token=os.getenv('ANTIDEVTROS_TOKEN'))
    else:
        main()


# endregion[Main_Exec]
