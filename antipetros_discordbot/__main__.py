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
import click
from dotenv import load_dotenv
import platform
import gidlogger as glog
from discord.ext import ipc
from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus
import json
from typing import List, Callable, Union, Optional, Iterable

# endregion[Imports]

# region [TODO]


# endregion [TODO]


# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
BASE_CONFIG.save()
COGS_CONFIG.save()
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


# endregion [Constants]

# region [Logging]


def filter_asyncio_call(record: logging.LogRecord):
    """
    filters the asyncio logger to only log calls that show if something is blocking.
    """

    if record.for_asyncio_enabled is True:
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

    # writejson([n for n in logging.root.manager.loggerDict], "loggers.json", default=str)
    log_stdout = 'both' if from_config('log_also_to_stdout', 'getboolean') is True else 'file'
    log_level = from_config('logging_level', 'get')
    _log_file = glog.timestamp_log_folderer(os.getenv('APP_NAME'), APPDATA)
    for file in os.scandir(os.path.dirname(_log_file)):
        if file.is_file() and file.name.endswith('.log'):
            try:
                shutil.move(file.path, pathmaker(os.path.dirname(file.path), 'old_logs'))
            except shutil.Error:
                shutil.move(file.path, pathmaker(os.path.dirname(file.path), 'old_logs', file.name.split('.')[0] + '_1.log'))
    limit_log_backups(pathmaker(os.path.dirname(_log_file), 'old_logs'))
    in_back_up = from_config('amount_keep_old_logs', 'getint')
    use_logging = from_config('use_logging', 'getboolean')
    if os.getenv('IS_DEV') == 'true':
        log_stdout = 'both'
    other_logger_names = BASE_CONFIG.retrieve('logging', 'other_logger_names', typus=List[str], direct_fallback=[])
    _log = glog.main_logger(_log_file, log_level, other_logger_names=other_logger_names, log_to=log_stdout, in_back_up=in_back_up)
    gidconfig_logger = logging.getLogger('gidconfig')
    gidconfig_logger.setLevel('DEBUG')
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.setLevel('WARNING')
    # asyncio_logger.addFilter(filter_asyncio_call)
    old_record_factory = logging.getLogRecordFactory()

    def asyncio_mod_message_factory(*args, **kwargs):
        record = old_record_factory(*args, **kwargs)

        if record.name == 'asyncio':
            if record.msg.startswith('Executing'):
                old_msg = record.msg
                new_msg = '!' * 10 + " " + "Loop was blocked for " + old_msg.split(" took ")[-1] + ' ' + '!' * 10
                record.msg = new_msg
                record.args = record.args[-1]
                record.for_asyncio_enabled = True
            else:
                record.for_asyncio_enabled = False

        return record

    # logging.setLogRecordFactory(asyncio_mod_message_factory)
    if use_logging is False:
        logging.disable(logging.CRITICAL)
    if os.getenv('IS_DEV') == 'yes':
        _log.warning('!!!!!!!!!!!!!!!!!!! IS DEV !!!!!!!!!!!!!!!!!!!')
        _log.warning('!!!!!!!!!!!!!!!!! DEBUG MODE !!!!!!!!!!!!!!!!!')
    return _log


# endregion[Logging]


# region [Helper]
def get_cog_states(cog_object):
    return CogMetaStatus.split(cog_object.docattrs['is_ready'][0])

# endregion [Helper]

# region [Main_function]


@click.group()
def cli():
    """
    dummy function to initiate click group.
    """


@cli.command(name="app-data-info")
def app_data_info():
    print(json.dumps(ParaStorageKeeper.serialize()))


@cli.group()
def collect_data():
    """
    dummy function to initiate click group.
    """


@collect_data.command(name='all')
@click.option('--output-file', '-o', default=None)
@click.option('--verbose', '-v', type=bool, default=False)
def command_info_run(output_file, verbose):
    """
    Cli command to start up the bot, collect bot-commands extended info, but not connect to discord.

    collected in `/docs/resources/data` as `commands_data.json`
    """
    old_cwd = os.getcwd()
    os.chdir(THIS_FILE_DIR)
    load_dotenv('token.env')
    load_dotenv("nextcloud.env")
    os.chdir(old_cwd)
    os.environ['INFO_RUN'] = "1"
    os.environ['INFO_RUN_DUMP_FOLDER'] = output_file
    if verbose is False:
        logging.disable(logging.CRITICAL)

    anti_petros_bot = AntiPetrosBot(token=os.getenv('ANTIDEVTROS_TOKEN'), ipc_key=os.getenv('IPC_SECRET_KEY'))

    print('#' * 15 + ' finished collecting command-infos ' + '#' * 15)


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
@click.option('--member-id', '-id', type=int)
def stop(member_id):
    """
    Not Implemented
    """
    raise NotImplementedError("not yet found good solution")


@cli.command(name='fill-config-run')
@ click.option('--token', '-t')
@ click.option('--nextcloud-username', '-nu', default=None)
@ click.option('--nextcloud-password', '-np', default=None)
@ click.option('--github-token', '-gt', default=None)
@ click.option('--battlemetrics-token', '-bt', default=None)
def fill_config_run(token, nextcloud_username, nextcloud_password, github_token, battlemetrics_token):

    os.environ['CONFIG_FILL_RUN'] = "1"
    main(token=str(token), nextcloud_username=nextcloud_username, nextcloud_password=nextcloud_password, github_token=github_token, battlemetrics_token=battlemetrics_token)


@ cli.command(name='run')
@ click.option('--token', '-t')
@ click.option('--nextcloud-username', '-nu', default=None)
@ click.option('--nextcloud-password', '-np', default=None)
@ click.option('--github-token', '-gt', default=None)
@ click.option('--battlemetrics-token', '-bt', default=None)
def run(token, nextcloud_username, nextcloud_password, github_token, battlemetrics_token):
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
    main(token=str(token), nextcloud_username=nextcloud_username, nextcloud_password=nextcloud_password, github_token=github_token, battlemetrics_token=battlemetrics_token)


def main(token: str, nextcloud_username: str = None, nextcloud_password: str = None, github_token: str = None, battlemetrics_token: str = None):
    """
    Starts the Antistasi Discord Bot 'AntiPetros'.

    Instantiates the bot, loads the extensions and starts the bot with the Token.
    This is seperated from the Cli run function so the bot can be started via cli but also from within vscode.

    Args:
        token_file ([str]): discord token
        nextcloud_username([str]): username for dev_drive on nextcloud
        nexctcloud_password([str]): password for dev_drive on nextcloud
    """
    log = configure_logger()
    log.info(glog.NEWRUN())
    operating_system_name = platform.system()
    log.info("Operating System is '%s'", operating_system_name)

    if operating_system_name == 'Linux':
        log.info("Trying to use 'uvloop', because the operating system is 'Linux'")
        try:
            import uvloop
            uvloop.install()
        except Exception as error:
            log.error(error)
            log.warning("Unable to use 'uvloop', falling back to default asyncio loop!")

    if nextcloud_username is not None:
        os.environ['NEXTCLOUD_USERNAME'] = nextcloud_username
    if nextcloud_password is not None:
        os.environ['NEXTCLOUD_PASSWORD'] = nextcloud_password
    if github_token is not None:
        os.environ['GITHUB_TOKEN'] = github_token
    if battlemetrics_token is not None:
        os.environ['BATTLEMETRICS_TOKEN'] = battlemetrics_token

    os.environ['INFO_RUN'] = "0"

    anti_petros_bot = AntiPetrosBot(token=token)
    log.info("Connecting Bot")

    try:
        anti_petros_bot.run()
        log.info('~+~' * 20 + ' finished shutting down! ' + '~+~' * 20)
    finally:
        log.info('~+~' * 20 + ' Bot has stopped ' + '~+~' * 20)

# endregion [Main_function]
# region [Main_Exec]


if __name__ == '__main__':

    if os.getenv('IS_DEV') == 'true':
        load_dotenv('token.env')
        load_dotenv("nextcloud.env")

        main(token=os.getenv('ANTIDEVTROS_TOKEN'),
             nextcloud_username=os.getenv('NEXTCLOUD_USERNAME'),
             nextcloud_password=os.getenv("NEXTCLOUD_PASSWORD_ANTIDEVTROS"),
             github_token=os.getenv('GITHUB_TOKEN'),
             battlemetrics_token=os.getenv('BATTLEMETRICS_TOKEN'))
    else:
        main()


# endregion[Main_Exec]
