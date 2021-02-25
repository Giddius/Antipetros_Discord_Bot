# region [Module_Docstring]

"""
Main module, starts the Antistasi Discord Bot.

On the Cli use:
    >>> antipetrosbot run [-t token]

"""
# endregion [Module_Docstring]


# region [Imports]
import shutil
import os
import logging
from time import sleep
from datetime import datetime
import click
from dotenv import load_dotenv
import gidlogger as glog
from antipetros_discordbot.utility.misc import generate_base_cogs_config, generate_help_data, save_commands
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

# endregion[Imports]

# region [TODO]


# endregion [TODO]


# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
BASE_CONFIG.save()
COGS_CONFIG.save()

# endregion [Constants]

# region [Logging]


def filter_asyncio_call(record: logging.LogRecord):
    """
    filters the asyncio logger to only log calls that show if something is blocking.

    """
    if record.getMessage().startswith('Executing'):
        return 1
    return 0


def limit_log_backups(backup_folder):
    all_files = []
    for file in os.scandir(backup_folder):
        if file.is_file():
            all_files.append((file.path, os.stat(file.path).st_ctime))
    all_files = sorted(all_files, key=lambda x: x[1])
    amount_to_keep = BASE_CONFIG.getint('logging', "amount_keep_old_logs")
    while len(all_files) > amount_to_keep:
        to_delete = all_files.pop(0)
        os.remove(to_delete[0])


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
    _log_file = glog.timestamp_log_folderer(os.getenv('APP_NAME'), APPDATA)
    for file in os.scandir(os.path.dirname(_log_file)):
        if file.is_file() and file.name.endswith('.log'):
            shutil.move(file.path, pathmaker(os.path.dirname(file.path), 'old_logs'))
    limit_log_backups(pathmaker(os.path.dirname(_log_file), 'old_logs'))
    in_back_up = from_config('amount_keep_old_logs', 'getint')
    use_logging = from_config('use_logging', 'getboolean')
    if os.getenv('IS_DEV') == 'true':
        log_stdout = 'both'

    _log = glog.main_logger(_log_file, log_level, other_logger_names=['asyncio', 'gidsql', 'gidfiles', "gidappdata"], log_to=log_stdout, in_back_up=in_back_up)
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.addFilter(filter_asyncio_call)
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
    Cli command to start up the bot, collect bot-commands extended info, but not connect to discord.

    collected in `/docs/resources/data` as `commands.json`, `command_help.json`

    """
    os.environ['INFO_RUN'] = "1"
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
    """
    Cli command to start up the bot, collect config prototype files, but not connect to discord.

    collected in `/docs/resources/prototype_files` as `standard_cogs_config.ini`, `standard_base_config.ini`

    """
    os.environ['INFO_RUN'] = "1"
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
    """
    Cli command to start up the bot, collect help info data, but not connect to discord.

    collected in `/docs/resources/data` as `command_help.json`

    """
    os.environ['INFO_RUN'] = "1"
    if verbose is False:
        logging.disable(logging.CRITICAL)
    anti_petros_bot = AntiPetrosBot()
    for cog_name, cog_object in anti_petros_bot.cogs.items():
        print(f"Collecting help-data for '{cog_name}'")
        generate_help_data(cog_object, output_file=output_file)
    print('#' * 15 + ' finished collecting help-data ' + '#' * 15)


@cli.command(name="clean")
def clean_user_data():
    """
    Cli command to clean the 'APPDATA' folder that was created.

    Deletes all files, created by this application in the `APPDATA` folder.

    Can be seen as a deinstall command.

    Raises:
        RuntimeError: if you try to delete the folder while `IS_DEV` is set, it raises andd error so not to delete the dev `APPDATA` folder.
    """
    if os.environ['IS_DEV'].casefold() in ['true', 'yes', '1'] or APPDATA.dev is True:
        raise RuntimeError("Cleaning not possible in Dev Mode")
    APPDATA.clean(APPDATA.AllFolder)


@cli.command(name='stop')
def stop():
    """
    Cli way of autostoping the bot.
    Writes a file to a specific folder that acts like a shutdown trigger (bot watches the folder)
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
@click.option('--nextcloud-username', '-nu', default=None)
@click.option('--nextcloud-password', '-np', default=None)
def run(token, nextcloud_username, nextcloud_password):
    """
    Standard way to start the bot and connect it to discord.
    takes the token as string and the key to decrypt the db also as string.
    calls the actual main() function.

    Args:
        token_file ([str]): discord token
        nextcloud_username([str]): username for dev_drive on nextcloud
        nexctcloud_password([str]): password for dev_drive on nextcloud
    """
    os.environ['INFO_RUN'] = "0"
    main(token=str(token), nextcloud_username=nextcloud_username, nextcloud_password=nextcloud_password)


def main(token: str, nextcloud_username: str = None, nextcloud_password: str = None):
    """
    Starts the Antistasi Discord Bot 'AntiPetros'.

    Instantiates the bot, loads the extensions and starts the bot with the Token.
    This is seperated from the Cli run function so the bot can be started via cli but also from within vscode.

    Args:
        token_file ([str]): discord token
        nextcloud_username([str]): username for dev_drive on nextcloud
        nexctcloud_password([str]): password for dev_drive on nextcloud
    """
    log.info(glog.NEWRUN())
    if nextcloud_username is not None:
        os.environ['NEXTCLOUD_USERNAME'] = nextcloud_username
    if nextcloud_password is not None:
        os.environ['NEXTCLOUD_PASSWORD'] = nextcloud_password
    os.environ['INFO_RUN'] = "0"
    anti_petros_bot = AntiPetrosBot(token=token)

    anti_petros_bot.run()


# endregion [Main_function]
# region [Main_Exec]
if __name__ == '__main__':
    if os.getenv('IS_DEV') == 'true':
        load_dotenv('token.env')
        load_dotenv("nextcloud.env")

        main(token=os.getenv('ANTIDEVTROS_TOKEN'), nextcloud_username=os.getenv('NX_USERNAME'), nextcloud_password=os.getenv("NX_PASSWORD"))
    else:
        main()


# endregion[Main_Exec]
