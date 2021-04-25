"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import os
import re
import random
import asyncio
from asyncstdlib import map as async_map
import random
from typing import Union
from datetime import datetime
from tempfile import TemporaryDirectory
from functools import partial, cached_property
from concurrent.futures import ThreadPoolExecutor
from dateparser import parse as date_parse
from asyncio import get_event_loop
# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

# import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

# from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process
from async_property import async_property, async_cached_property
from webdav3.client import Client
# * PyQt5 Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

# from PyQt5.QtGui import QFont, QIcon, QBrush, QColor, QCursor, QPixmap, QStandardItem, QRegExpValidator

# from PyQt5.QtCore import (Qt, QRect, QSize, QObject, QRegExp, QThread, QMetaObject, QCoreApplication,
#                           QFileSystemWatcher, QPropertyAnimation, QAbstractTableModel, pyqtSlot, pyqtSignal)

# from PyQt5.QtWidgets import (QMenu, QFrame, QLabel, QAction, QDialog, QLayout, QWidget, QWizard, QMenuBar, QSpinBox, QCheckBox, QComboBox, QGroupBox, QLineEdit,
#                              QListView, QCompleter, QStatusBar, QTableView, QTabWidget, QDockWidget, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout,
#                              QHeaderView, QListWidget, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWizardPage,
#                              QApplication, QButtonGroup, QRadioButton, QFontComboBox, QStackedWidget, QListWidgetItem, QSystemTrayIcon, QTreeWidgetItem,
#                              QDialogButtonBox, QAbstractItemView, QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator)


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog

# from gidtools.gidfiles import (readit, clearit, readbin, writeit, loadjson, pickleit, writebin, pathmaker, writejson,
#                                dir_change, linereadit, get_pickled, ext_splitter, appendwriteit, create_folder, from_dict_to_file)


# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import bytes2human, pathmaker, readit, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.regexes import LOG_NAME_DATE_TIME_REGEX, LOG_SPLIT_REGEX, MOD_TABLE_START_REGEX, MOD_TABLE_END_REGEX, MOD_TABLE_LINE_REGEX
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antipetros_discordbot.utility.misc import SIZE_CONV_BY_SHORT_NAME
from antipetros_discordbot.utility.general_decorator import debug_timing_log
from antipetros_discordbot.utility.misc import async_list_iterator, async_dict_items_iterator
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class LogFile:
    size_string_regex = re.compile(r"(?P<number>\d+)\s?(?P<unit>\w+)")
    loop = asyncio.get_event_loop()

    def __init__(self, created, etag, isdir, modified, name, path, size):
        self.etag = etag.strip('"')
        self.isdir = isdir
        self.modified = date_parse(modified, settings={'TIMEZONE': 'UTC'})
        self.name = name if name is not None else os.path.basename(path)
        self.full_path = path
        self.path = '/'.join(path.split('/')[6:])
        self.created = date_parse(created, settings={'TIMEZONE': 'UTC'}) if created is not None else self._date_time_from_name()
        self.size = int(size)
        self.server_name = self.path.split('/')[1]
        self.sub_folder_name = self.path.split('/')[2]
        self.latest_parsed_time = None
        self.campaign_id = 000000

    @async_property
    async def mod_data(self):
        _out = []
        content = await self.content()
        split_match = LOG_SPLIT_REGEX.search(content)
        if split_match:
            pre_content = content[:split_match.end()]
            cleaned_lower = MOD_TABLE_START_REGEX.split(pre_content)[-1]
            mod_table = MOD_TABLE_END_REGEX.split(cleaned_lower)[0]
            for line in mod_table.splitlines():
                if line != '':
                    line_match = MOD_TABLE_LINE_REGEX.search(line)
                    _out.append({key: value.strip() for key, value in line_match.groupdict().items()})
            return [item.get('mod_dir') for item in _out if item.get('official') == 'false' and item.get("mod_name") not in ["@members", "@TaskForceEnforcer", "@utility"]]

    @cached_property
    def warning_size_threshold(self):
        limit = COGS_CONFIG.retrieve('antistasi_log_watcher', 'log_file_warning_size_threshold', typus=str, direct_fallback='200mb')
        match_result = self.size_string_regex.search(limit)
        relative_size = int(match_result.group('number'))
        unit = match_result.group('unit').casefold()
        return relative_size * SIZE_CONV_BY_SHORT_NAME.get(unit)

    @property
    def size_pretty(self):
        return bytes2human(self.size, annotate=True)

    @cached_property
    def created_pretty(self):
        return self.created.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def modified_pretty(self):
        return self.modified.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_over_threshold(self):
        if self.size >= self.warning_size_threshold:
            return True
        return False

    def _date_time_from_name(self):
        matched_data = LOG_NAME_DATE_TIME_REGEX.search(os.path.basename(self.full_path))
        if matched_data:
            date_time_string = f"{matched_data.group('year')}-{matched_data.group('month')}-{matched_data.group('day')} {matched_data.group('hour')}:{matched_data.group('minute')}:{matched_data.group('second')}"
            date_time = datetime.strptime(date_time_string, "%Y-%m-%d %H:%M:%S")
            return date_time
        else:
            raise RuntimeError(f'unable to find date_time_string in {os.path.basename(self.full_path)}')

    async def content(self):
        client = Client(get_nextcloud_options())
        with TemporaryDirectory() as tempdir:
            new_path = pathmaker(tempdir, os.path.basename(self.path))
            await asyncio.to_thread(client.download_sync, self.path, new_path)

            content = await asyncio.to_thread(readit, new_path)

            return content

    async def download(self, save_dir):
        client = Client(get_nextcloud_options())
        new_path = pathmaker(save_dir, os.path.basename(self.path))

        await asyncio.to_thread(client.download_sync, self.path, new_path)

        return new_path

    async def update(self, size: Union[str, int], modified: Union[datetime, str], first: bool = False):
        if isinstance(size, str):
            size = int(size)
        if isinstance(modified, str):
            modified = date_parse(modified)

        # if first is True:
        # current_time = datetime.utcnow()
        # log.debug(ic.format(self.path))
        # log.debug(ic.format(current_time.strftime("%Y-%m-%d %H:%M:%S")))
        # log.debug(ic.format(modified.strftime("%Y-%m-%d %H:%M:%S")))
        # log.debug(ic.format(self.modified.strftime("%Y-%m-%d %H:%M:%S")))
        # log.debug(ic.format(size))
        # log.debug(ic.format(self.size))
        # log.debug('#' * 50 + '\n\n')

        if self.size != size or self.modified < modified:
            self.size = size
            self.modified = modified
            log.info("!LOG_ITEM_UPDATED! log_item '%s' with path '%s' was updated", self.name, self.path)

    async def dump(self):
        return {"etag": self.etag,
                "isdir": self.isdir,
                "modified": self.modified.strftime("%Y-%m-%d %H:%M:%S"),
                "name": self.name,
                "full_path": self.full_path,
                "path": self.path,
                "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
                "size": self.size,
                "size_pretty": self.size_pretty}

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with path '{self.path}'"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" + ', '.join(map(str, [self.created.strftime("%Y-%m-%d %H:%M:%S"), self.etag, self.isdir, self.modified.strftime("%Y-%m-%d %H:%M:%S"), self.name, self.full_path, self.path, self.size, self.size_pretty])) + ')'


class LogServer:
    log_item = LogFile

    def __init__(self, base_folder: str, name: str):
        self.base_folder = base_folder
        self.name = name
        self.sub_folder = None
        self.path = f"{self.base_folder}/{self.name}"

    async def get_data(self):
        client = Client(get_nextcloud_options())
        log.debug("collecting initial data for LogServer '%s'", self.name)
        self.sub_folder = {}
        sub_folder_names = await asyncio.to_thread(client.list, self.path)
        for sub_folder_name in sub_folder_names:
            sub_folder_name = sub_folder_name.strip('/')
            if sub_folder_name != self.name:
                file_infos = await self.get_file_infos(sub_folder_name)
                self.sub_folder[sub_folder_name] = await asyncio.to_thread(sorted, file_infos, key=lambda x: x.modified, reverse=True)
            await asyncio.sleep(0)
        log.info(self.path + ' collected subfolder: ' + ', '.join([key for key in self.sub_folder]))

    async def get_file_infos(self, sub_folder_name, raw=False):
        client = Client(get_nextcloud_options())
        _out = []
        file_data_list = await asyncio.to_thread(client.list, f"{self.path}/{sub_folder_name}", get_info=True)
        async for file_data in async_list_iterator(file_data_list):
            if not file_data.get('path').endswith('/'):
                if raw is True:
                    _out.append(file_data)
                else:
                    item = self.log_item(**file_data)
                    _out.append(item)

        return _out

    async def get_newest_log_file(self, sub_folder, amount):
        _out = []
        mod_sub_folder = sub_folder.casefold()
        if mod_sub_folder not in {sub_folder_name.casefold() for sub_folder_name in self.sub_folder}:
            raise KeyError(f'Unable to find a subfolder with the name of "{sub_folder}"')
        for sub_folder_name in self.sub_folder:
            if sub_folder_name.casefold() == mod_sub_folder:
                file_list = await asyncio.to_thread(sorted, self.sub_folder[sub_folder_name], key=lambda x: x.modified, reverse=True)
                for i in range(amount):
                    newest_file = file_list[i]
                    _out.append(newest_file)
        return _out

    async def update(self):
        _temp_holder = {}
        for sub_folder_name in self.sub_folder:
            _temp_holder[sub_folder_name] = await self.get_file_infos(sub_folder_name, raw=True)
            for new_log_item_data in _temp_holder[sub_folder_name]:
                await self.update_log_items(sub_folder_name, **new_log_item_data)

            self.sub_folder[sub_folder_name] = await asyncio.to_thread(sorted, self.sub_folder[sub_folder_name], key=lambda x: x.modified, reverse=True)

    async def update_log_items(self, sub_folder_name, ** data_kwargs):
        path = data_kwargs.get('path')
        path = '/'.join(path.split('/')[6:])
        target_log_object = None
        for index, log_object in enumerate(self.sub_folder.get(sub_folder_name)):
            if path == log_object.path:
                target_log_object = log_object
                target_index = index
                break

        if target_log_object is not None:
            first = target_index == 0
            await target_log_object.update(data_kwargs.get('size'), data_kwargs.get('modified'), first=first)
        else:
            new_log_item = self.log_item(**data_kwargs)
            self.sub_folder[sub_folder_name].append(new_log_item)
            self.sub_folder[sub_folder_name] = await asyncio.to_thread(sorted, self.sub_folder[sub_folder_name], key=lambda x: x.modified, reverse=True)
            log.info("!NEW LOG ITEM! added new log_item '%s' to LogServer('%s', '%s')", new_log_item.name, self.name, sub_folder_name)

    async def sort(self):
        async for sub_folder_name in async_list_iterator(self.sub_folder):
            self.sub_folder[sub_folder_name] = await asyncio.to_thread(sorted, self.sub_folder[sub_folder_name], key=lambda x: x.modified, reverse=True)

    async def get_oversized_items(self):
        oversized_items = []
        for sub_folder_name, log_items in self.sub_folder.items():
            for log_item in log_items:
                if log_item.is_over_threshold is True:
                    oversized_items.append(log_item)
        return oversized_items

    async def dump(self, file_name):
        _out = {"name": self.name, "path": self.path, "sub_folder": {}}
        for sub_folder_name, log_items in self.sub_folder.items():
            if sub_folder_name not in _out["sub_folder"]:
                _out["sub_folder"][sub_folder_name] = []
            for item in log_items:
                _out["sub_folder"][sub_folder_name].append(await item.dump())
        writejson(_out, file_name)

        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
