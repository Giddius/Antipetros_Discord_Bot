# * Local Imports -->
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
import os
import importlib.util
from importlib import import_module
from functools import lru_cache

APPDATA = ParaStorageKeeper.get_appdata()


def get_aliases(command_name):
    data = loadjson(APPDATA['command_aliases.json'])
    return data.get(command_name, [])


def get_brief(command_name):
    data = loadjson(APPDATA['command_meta_data.json'])
    return data.get(command_name, {}).get('brief', None)


def get_description(command_name):
    data = loadjson(APPDATA['command_meta_data.json'])
    return data.get(command_name, {}).get('description', "")


def get_usage(command_name):
    data = loadjson(APPDATA['command_meta_data.json'])
    return data.get(command_name, {}).get('usage', None)


def get_help(command_name):
    data = loadjson(APPDATA['command_meta_data.json'])
    return data.get(command_name, {}).get('help', None)


def get_doc_data(command_name):
    return loadjson(APPDATA['command_meta_data.json']).get(command_name, {"brief": None, "description": "", "help": None, "usage": None})


COGS_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.islink(COGS_DIR) is True:

    COGS_DIR = os.readlink(COGS_DIR).replace('\\\\?\\', '').replace(os.pathsep, '/')


def get_cog_paths_from_folder(folder_name: str, files_to_exclude: list = None):
    """
    gets all relative import paths(only missing the commong import path at the front) for files in a subfolder.

    Convinence function, to not have to specify each import path manually.

    Args:
        folder_name `str`: name of the subfolder.
        files_to_exclude `list`: list of files to exclude when collecting import paths.

    Returns:
        `list`: collected import paths from the subfolder.
    """
    import_paths = []
    files_to_exclude = [] if files_to_exclude is None else files_to_exclude
    files_to_exclude = set(map(lambda x: x.casefold(), files_to_exclude + ['__init__.py']))
    for cog_file in os.scandir(os.path.join(COGS_DIR, folder_name)):
        if cog_file.is_file() and cog_file.name != '__init__.py' and cog_file.name.casefold() not in files_to_exclude:
            folder = os.path.basename(os.path.dirname(cog_file.path))
            name = cog_file.name.split('.')[0]
            import_paths.append(f"{folder}.{name}")
    return import_paths


BOT_ADMIN_COG_PATHS = get_cog_paths_from_folder(folder_name='bot_admin_cogs', files_to_exclude=['bot_development_organization_cog.py', 'bot_feedback_cog.py'])
DEV_COG_PATHS = get_cog_paths_from_folder(folder_name='dev_cogs', files_to_exclude=[])
DISCORD_ADMIN_COG_PATHS = get_cog_paths_from_folder(folder_name='discord_admin_cogs', files_to_exclude=[])
