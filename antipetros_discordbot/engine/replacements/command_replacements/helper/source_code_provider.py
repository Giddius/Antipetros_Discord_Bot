"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

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
from typing import Union, Callable, Iterable, List, Dict, Optional, Tuple, Any, Callable, Mapping, TYPE_CHECKING
from zipfile import ZipFile
from datetime import tzinfo, datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
import inspect

# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process

from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters

# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, TomorrownighteightiesStyle, TomorrownightblueStyle, TomorrownightbrightStyle, TomorrownightStyle, TomorrowStyle
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class SourceCodeProvider:
    base_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/blob/development/"
    base_folder_name = 'antipetros_discordbot'
    code_highlighter_style = DraculaStyle

    def __init__(self, command: commands.Command):
        self.command = command

    @cached_property
    def line_numbers(self) -> tuple:
        source_lines = inspect.getsourcelines(self.command.callback)
        start_line_number = source_lines[1]
        code_length = len(source_lines[0])
        code_line_numbers = tuple(range(start_line_number, start_line_number + code_length))
        return code_line_numbers

    @cached_property
    def github_line_link(self) -> str:
        rel_path = self.antipetros_repo_rel_path(inspect.getsourcefile(self.command.cog.__class__))
        code_line_numbers = self.line_numbers
        full_path = self.base_url + rel_path + f'#L{min(code_line_numbers)}-L{max(code_line_numbers)}'
        return full_path

    def antipetros_repo_rel_path(self, in_path: str) -> str:
        in_path = pathmaker(in_path)
        in_path_parts = in_path.split('/')
        while in_path_parts[0] != self.base_folder_name:
            _ = in_path_parts.pop(0)
        return pathmaker(*in_path_parts)

    async def source_code_image(self) -> bytes:
        rel_path = self.antipetros_repo_rel_path(inspect.getsourcefile(self.command.cog.__class__))
        raw_source_code = f'\t# {rel_path}\n\n' + inspect.getsource(self.command.callback)

        image = highlight(raw_source_code, PythonLexer(), ImageFormatter(style=self.code_highlighter_style,
                                                                         font_name='Fira Code',
                                                                         line_number_start=min(self.line_numbers),
                                                                         line_number_bg="#2f3136",
                                                                         line_number_fg="#ffffff",
                                                                         line_number_chars=3,
                                                                         line_pad=5,
                                                                         font_size=20,
                                                                         line_number_bold=True))
        return image


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
