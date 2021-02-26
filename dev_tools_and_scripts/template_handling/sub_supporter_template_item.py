"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import os
import re
import sys
import json
import lzma
import time
import queue
import base64
import pickle
import random
import shelve
import shutil
import asyncio
import logging
import sqlite3
import platform
import importlib
import subprocess
import unicodedata
from io import BytesIO
from abc import ABC, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import Dict, Union, Callable, Iterable
from inspect import stack, getdoc, getmodule, getsource, getmembers, getmodulename, getsourcefile, getfullargspec, getsourcelines
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader

# * Third Party Imports --------------------------------------------------------------------------------->
import autopep8

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import split_camel_case_string
from antipetros_discordbot.utility.exceptions import CogNameNotCamelCaseError
from antipetros_discordbot.bot_support.sub_support import SUB_SUPPORT_DIR
from antipetros_discordbot.utility.gidtools_functions import pathmaker, create_file, create_folder
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.dev_tools_and_scripts.data.event_data import EVENT_MAPPING
from antipetros_discordbot.dev_tools_and_scripts.template_handling.templates import TEMPLATES_DIR, TEMPLATE_MANAGER

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class SubSupporterTemplateItem:
    standard_template_name = 'sub_supporter_template.py.jinja'
    template_var_name = 'sub_support'

    def __init__(self, name: str, responsibility: str, format_code: bool = True, overwrite: bool = False) -> None:
        self.name = name
        self._check_name()
        self.description = {'text': '', 'responsibility': responsibility}
        self._template_name = self.standard_template_name
        self.overwrite = overwrite
        self.format_code = format_code
        self._code = None
        self.dependencies = []

    def add_dependency(self, dependency):
        self.dependencies.append(dependency)

    def add_description_text(self, text: Union[str, Iterable[str]]):
        if any(isinstance(text, typus) for typus in [list, set, tuple]):
            text = '\n'.join(text)
        self.description['text'] = text

    @property
    def code(self):
        code = self._render()
        if self.format_code is True:
            print("formatting code with autopep8")
            return autopep8.fix_code(code)
        return code

    @property
    def file_path(self):
        return pathmaker(SUB_SUPPORT_DIR, self.file_name)

    @property
    def file_name(self):
        return self._alt_name + '.py'

    @property
    def _alt_name(self):
        return split_camel_case_string(self.name).replace(' ', '_').lower()

    @property
    def template_name(self):
        return self._template_name

    @template_name.setter
    def template_name(self, value: str):
        if not value.endswith('.jinja'):
            value = value + '.jinja'

        if value not in TEMPLATE_MANAGER:
            raise KeyError(f'unknown template name "template_name={value}"')

        self._template_name = value

    @property
    def template(self):
        return TEMPLATE_MANAGER.fetch_template(self.template_name)

    @code.setter
    def code(self, value: str):
        if value in [None, '']:
            raise ValueError(f"cannot set '{value=}'' as value for 'code'")

        self._code = value

    def _check_name(self):
        if any(char.upper() == char for char in self.name) is False or any(forbidden_char in self.name for forbidden_char in ['_', ' ']):
            raise CogNameNotCamelCaseError(f'SubSupporter name must be camel case not "{self.name}"')

    def _render(self):
        return self.template(**{self.template_var_name: self})

    def write(self):
        if self._code in [None, '']:
            raise AttributeError(f'code attribute is {self._code}')
        if os.path.isfile(self.file_path) is True and self.overwrite is False:
            raise FileExistsError(f"SubSupporter file '{self.file_path}' allready exists and '{self.overwrite=}'")
        with open(self.file_path, 'w') as f:
            f.write(self.code)

    def generate(self):
        self.code = self._render()
        self.write()

# region[Main_Exec]


if __name__ == '__main__':
    x = SubSupporterTemplateItem('BlacklistWarden', 'managing and querying the blacklist of Users')
    x.generate()

# endregion[Main_Exec]
