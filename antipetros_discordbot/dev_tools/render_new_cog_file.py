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
from configparser import ConfigParser
# * Third Party Imports -->
# import pyperclip
# from dotenv import load_dotenv
from jinja2 import BaseLoader, Environment, FileSystemLoader
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process


# * Gid Imports -->
import gidlogger as glog
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit, readit, readbin, writebin, appendwriteit, linereadit, writejson, loadjson, pickleit, get_pickled

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.named_tuples import NEW_COG_ITEM, NEW_COMMAND_ITEM, NEW_LISTENER_ITEM, NEW_LOOP_ITEM
# endregion[Imports]


# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
TEMPLATE_PATH = APPDATA['python']

ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH, encoding='utf-8'))

# endregion[Constants]


def _render(template_name: str, in_item: namedtuple, variable_name: str):
    # sourcery skip: inline-immediately-returned-variable
    template = ENV.get_template(template_name + '.py.jinja')
    completed_item = in_item._replace(code=template.render({variable_name: in_item}))
    return completed_item


def _render_new_loop(loop_item: namedtuple):

    return _render('loop_template', loop_item, 'loop_item')


def _render_new_listener(listener_item: namedtuple):

    return _render('listener_template', listener_item, 'listener_item')


def _render_new_command(command_item: namedtuple):

    return _render('command_template', command_item, 'command_item')


def _render_new_cog(cog_item: namedtuple):

    return _render('cog_template', cog_item, 'cog_item')


ITEM_HANDLING = {'NewCommandItem': _render_new_command,
                 'NewListenerItem': _render_new_listener,
                 'NewLoopItem': _render_new_loop}


def run_render(item):
    _render_func = ITEM_HANDLING.get(item.__class__.__name__)
    return _render_func(item)


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
    folder = pathmaker(os.path.dirname(file))
    for item_list_name in ["all_loops", "all_listeners", "all_commands"]:
        cog_item = cog_item._replace(**{item_list_name: list(map(run_render, getattr(cog_item, item_list_name)))})
    cog_item = _render_new_cog(cog_item)

    _make_folder(folder)
    if os.path.isfile(file) is False or overwrite is True:
        writeit(file, cog_item.code)
    _edit_configs(cog_item)

# region[Main_Exec]


if __name__ == '__main__':
    # _commands = []
    # _listener = []
    # _loops = []
    # _commands.append(NEW_COMMAND_ITEM('test_1', ''))
    # _commands.append(NEW_COMMAND_ITEM('test_2', ''))
    # _listener.append(NEW_LISTENER_ITEM('test_listener_1', 'on_message', ''))
    # _loops.append(NEW_LOOP_ITEM('test_loop_1', [('hour', 1)], ''))
    # x = NEW_COG_ITEM('test_cog_1', r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\cogs\general_cogs\test_cog.py",
    #                  "general_cogs.test_cog", 'test_cog', [('hidden', True)], _loops, _listener, _commands, ["import github"], '')
    # create_cog_file(x)
    pass
# endregion[Main_Exec]
