"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import os
import asyncio

from typing import Union
from datetime import datetime


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv



# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process

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


class GiveAwayEvent:
    bot = None

    def __init__(self, title: str, enter_emoji, end_message: str, amount_winners: int, end_date_time: Union[datetime, str], channel: Union[discord.TextChannel, int], message: Union[discord.Message, int], author: Union[discord.Member, int]):
        if self.bot is None:
            raise AttributeError('missing bot as class attributed')
        self.title = title
        self.enter_emoji = enter_emoji
        self.end_message = end_message
        self.amount_winners = amount_winners
        self.end_date_time = end_date_time
        self.channel = channel
        self.message = message
        self.author = author

    async def check_convert(self):
        self.end_date_time = await asyncio.wait_for(self.convert_datetime(self.end_date_time), timeout=None) if isinstance(self.end_date_time, str) else self.end_date_time
        self.channel = await asyncio.wait_for(self.convert_channel(self.channel), timeout=None) if isinstance(self.channel, int) else self.channel

        self.message = await asyncio.wait_for(self.convert_message(self.message), timeout=None) if isinstance(self.message, int) else self.message
        self.author = await asyncio.wait_for(self.convert_author(self.author), timeout=None) if isinstance(self.author, int) else self.author

    async def convert_datetime(self, in_date_time: Union[str, datetime]):
        if isinstance(in_date_time, datetime):
            return in_date_time.strftime(self.bot.std_date_time_format)
        elif isinstance(in_date_time, str):
            return datetime.strptime(in_date_time, self.bot.std_date_time_format)

    async def convert_channel(self, in_channel: Union[discord.TextChannel, int]):
        if isinstance(in_channel, discord.TextChannel):
            return in_channel.id
        elif isinstance(in_channel, int):
            return await self.bot.channel_from_id(in_channel)

    async def convert_message(self, in_message: Union[discord.Message, int]):
        if isinstance(in_message, discord.Message):
            return in_message.id
        elif isinstance(in_message, int):

            channel = self.channel if isinstance(self.channel, discord.TextChannel) else self.bot.get_channel(self.channel)
            return await channel.fetch_message(in_message)

    async def convert_author(self, in_author: Union[discord.Member, int]):
        if isinstance(in_author, discord.Member):
            return in_author.id
        elif isinstance(in_author, int):
            return await self.bot.retrieve_antistasi_member(in_author)

    async def to_dict(self):
        return {'title': self.title,
                'enter_emoji': self.enter_emoji,
                'end_message': self.end_message,
                'amount_winners': self.amount_winners,
                'end_date_time': await self.convert_datetime(self.end_date_time),
                'channel': await self.convert_channel(self.channel),
                'message': await self.convert_message(self.message),
                'author': await self.convert_author(self.author)}

    @classmethod
    async def from_dict(cls, in_data: dict):
        item = cls(**in_data)
        await item.check_convert()
        return item


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]