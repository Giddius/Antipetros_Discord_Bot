# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os

# * Third Party Imports --------------------------------------------------------------------------------->
# * Third Party Imports -->
import dotenv
from gidconfig import SingleAccessConfigHandler
from gidappdata import ParaStorageKeeper
from gidappdata.utility.extended_dotenv import find_dotenv_everywhere

from .bin_data import bin_archive_data
SingleAccessConfigHandler.set_default_setting("strict", False)
SingleAccessConfigHandler.set_default_setting("read_before_retrieve", True)
ParaStorageKeeper.set_special_config_handler(SingleAccessConfigHandler)
dotenv.load_dotenv(find_dotenv_everywhere('project_meta_data.env'))

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(THIS_FILE_DIR, 'data_pack')
CONSTRUCTION_INFO_FILE = os.path.join(THIS_FILE_DIR, 'construction_info.env')
DEV_TRIGGER_FILE = os.path.join(THIS_FILE_DIR, 'dev.trigger')

if os.path.isfile(CONSTRUCTION_INFO_FILE):
    dotenv.load_dotenv(CONSTRUCTION_INFO_FILE)

if os.path.isfile(DEV_TRIGGER_FILE) is True:
    ParaStorageKeeper.set_dev(True, DATA_DIR, os.getenv('LOG_FOLDER'))

ParaStorageKeeper.set_archive_data(bin_archive_data)
ParaStorageKeeper.app_info['app_name'] = os.getenv('APP_NAME').title()
ParaStorageKeeper.app_info['author_name'] = os.getenv('AUTHOR_NAME').title()
ParaStorageKeeper.app_info['uses_base64'] = True
