from gidappdata import SupportKeeper
from gidappdata.utility.extended_dotenv import find_dotenv_everywhere
import os
import dotenv
from .bin_data import bin_archive_data
import antipetros_discordbot
dotenv.load_dotenv(find_dotenv_everywhere('project_meta_data.env'))

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(THIS_FILE_DIR, 'data_pack')
CONSTRUCTION_INFO_FILE = os.path.join(THIS_FILE_DIR, 'construction_info.env')
DEV_TRIGGER_FILE = os.path.join(THIS_FILE_DIR, 'dev.trigger')

if os.path.isfile(CONSTRUCTION_INFO_FILE):
    dotenv.load_dotenv(CONSTRUCTION_INFO_FILE)

if os.path.isfile(DEV_TRIGGER_FILE) is True:
    SupportKeeper.set_dev(True, DATA_DIR, os.getenv('LOG_FOLDER'))
SupportKeeper.set_archive_data(bin_archive_data)
SupportKeeper.app_info['app_name'] = os.getenv('APP_NAME').title()
SupportKeeper.app_info['author_name'] = os.getenv('AUTHOR_NAME').title()
SupportKeeper.app_info['uses_base64'] = True
