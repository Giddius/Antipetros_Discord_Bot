# region [Imports]

# * Standard Library Imports -->
import os
from glob import iglob

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.gidtools_functions import work_in, pathmaker

# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process


# endregion[Imports]


# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


def find_path(path_fragment):
    """
    finds absolute path, to folder or file.


    Args:
        path_fragment (str): the fragment to find

    Returns:
        str: absolute path to the fragment
    """
    _main_dir = os.getenv('MAIN_DIR')
    with work_in(_main_dir):
        return pathmaker(os.path.abspath(list(iglob(f"**/{path_fragment}", recursive=bool))[0]))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
