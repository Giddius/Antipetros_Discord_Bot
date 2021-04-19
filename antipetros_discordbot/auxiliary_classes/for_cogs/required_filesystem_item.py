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
from enum import Enum, Flag, auto, unique
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


from marshmallow import Schema, fields
from antipetros_discordbot.utility.gidtools_functions import writejson, writeit, writebin, readit, loadjson, readbin, pathmaker
import gidlogger as glog


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


class RequiredFile:
    @unique
    class FileType(Enum):
        TEXT = auto()
        JSON = auto()

        def create(self, path, content):
            if self is self.TEXT:
                writeit(path, content)
            elif self is self.JSON:
                writejson(content, path)

        def __str__(self):
            return str(self.name)

    file_type_map = {'txt': FileType.TEXT,
                     'log': FileType.TEXT,
                     'md': FileType.TEXT,
                     'html': FileType.TEXT,
                     'env': FileType.TEXT,
                     'jinja': FileType.TEXT,
                     'json': FileType.JSON}

    def __init__(self, path, default_content, typus: Union[str, FileType] = None):
        self.path = pathmaker(path)
        self.name = os.path.basename(self.path)
        self.dir_path = os.path.dirname(self.path)
        self.default_content = default_content
        self.file_type = self.get_file_type(typus) if typus is None or isinstance(typus, str) else typus

    def get_file_type(self, in_typus) -> FileType:
        extension = self.name.split('.')[-1] if in_typus is None else in_typus.casefold()
        file_type = self.file_type_map.get(extension.casefold(), None)
        if file_type is None:
            raise TypeError(f"Required File '{self.path}' either has no extension or it is a directory and not a file")
        return file_type

    def ensure(self):
        if os.path.isdir(self.dir_path) is False:
            os.makedirs(self.dir_path)
        if os.path.isfile(self.path) is False:
            self.file_type.create(self.path, self.default_content)


class RequiredFolder:
    def __init__(self, path):
        self.path = pathmaker(path)
        self.name = os.path.basename(self.path)
        if '.' in self.name[1:]:
            raise TypeError(f"Required Folder '{self.path}' seems to be a file and not a directory")

    def ensure(self):
        if os.path.isdir(self.path) is False:
            os.makedirs(self.path)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
