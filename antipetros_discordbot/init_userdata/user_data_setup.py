from gidappdata import SupportKeeper
from gidappdata.utility.extended_dotenv import find_dotenv_everywhere
import os
import dotenv
from .bin_data import bin_archive_data
dotenv.load_dotenv(find_dotenv_everywhere('project_meta_data.env'))

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(THIS_FILE_DIR, 'data_pack')
CONSTRUCTION_INFO_FILE = os.path.join(THIS_FILE_DIR, 'construction_info.env')


if os.path.isfile(CONSTRUCTION_INFO_FILE):
    dotenv.load_dotenv(CONSTRUCTION_INFO_FILE)

if os.path.isfile('dev.trigger') is True:
    SupportKeeper.set_dev(True, DATA_DIR)
SupportKeeper.set_archive_data(bin_archive_data)
