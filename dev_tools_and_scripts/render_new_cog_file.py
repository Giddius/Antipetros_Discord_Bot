# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from collections import namedtuple

# * Third Party Imports --------------------------------------------------------------------------------->
import autopep8
from jinja2 import Environment, FileSystemLoader

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import COGS_DIR
from antipetros_discordbot.utility.named_tuples import NEW_COG_ITEM, NEW_LOOP_ITEM, NEW_COMMAND_ITEM, NEW_LISTENER_ITEM
from antipetros_discordbot.utility.gidtools_functions import writeit, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.dev_tools_and_scripts.templates import TEMPLATES_DIR

# endregion[Imports]


# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = pathmaker(os.path.abspath(os.path.dirname(__file__)))


ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR, encoding='utf-8'))

# endregion[Constants]
# for templates


def _render(template_name: str, in_cog_item):
    # sourcery skip: inline-immediately-returned-variable
    template = ENV.get_template(template_name + '.py.jinja')
    _code = template.render(cog_item=in_cog_item)
    if template_name == 'cog_template':
        _code = autopep8.fix_code(_code)

    return _code


def _edit_configs(cog_item: namedtuple):
    BASE_CONFIG.set('extensions', cog_item.import_location, 'no')
    COGS_CONFIG.add_section(cog_item.config_name)
    BASE_CONFIG.save()
    COGS_CONFIG.save()


def _make_folder(folder):
    if os.path.isdir(folder) is False:
        os.makedirs(folder)
        writeit(pathmaker(folder, '__init__.py'), '')


def create_cog_file(cog_item: namedtuple, overwrite=False):
    # IDEA: create gui for this
    file = pathmaker(cog_item.absolute_location)
    folder = pathmaker(cog_item.category_folder_path)

    _make_folder(folder)
    if os.path.isfile(file) is False or overwrite is True:
        writeit(file, cog_item.code)
    _edit_configs(cog_item)

# region[Main_Exec]


if __name__ == '__main__':

    pass
# endregion[Main_Exec]
