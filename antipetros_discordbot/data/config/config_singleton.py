# region [Imports]

# * Standard Library Imports -->
import gc
import os
import re
import sys
import json
import lzma
import time
import queue
import logging
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process


# * Gid Imports -->
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import pathmaker

from gidconfig import ConfigHandler

# endregion[Imports]

__updated__ = '2020-11-21 13:07:56'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

CONFIG_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_CONFIG = ConfigHandler(pathmaker(CONFIG_DIR, "base_config.ini"))
COGS_CONFIG = ConfigHandler(pathmaker(CONFIG_DIR, 'cogs_config.ini'))
# endregion[Constants]


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
