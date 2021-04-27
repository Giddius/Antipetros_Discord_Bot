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
from typing import Union, Callable, Iterable
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


import gidlogger as glog
from marshmallow import Schema, fields, pre_load

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

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AntiPetrosBaseCommandSchema(Schema):
    name = fields.Str(required=True)
    aliases = fields.List(fields.Str())
    enabled = fields.Bool()
    hidden = fields.Bool()
    help = fields.Str()
    brief = fields.Str()
    description = fields.Str()
    short_doc = fields.Str()
    usage = fields.Str()
    signature = fields.Str()
    example = fields.Str()
    gif = fields.Raw()
    github_link = fields.Str()
    allowed_channels = fields.List(fields.Str())
    allowed_roles = fields.List(fields.Str())
    allowed_in_dms = fields.Bool()
    allowed_members = fields.List(fields.Str())
    parent = fields.Nested(lambda: AntiPetrosBaseCommandSchema(), default=None)
    categories = fields.List(fields.Nested('CommandCategorySchema', exclude=('commands',)))

    class Meta:
        additional = ('_old_data', 'docstring')


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
