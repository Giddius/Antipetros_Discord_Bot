"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import asyncio
import unicodedata
import asyncio
from enum import Enum, auto


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->
import a2s

from async_property import async_property
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
from antipetros_discordbot.utility.exceptions import NeededClassAttributeNotSet, NeededConfigValueMissing
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
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
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# endregion[Constants]


class ServerStatusChange(Enum):
    TO_ON = auto()
    TO_OFF = auto()


class CommunityServerInfo:
    timeout = 1
    battle_metrics_mapping = {'mainserver_1': "https://www.battlemetrics.com/servers/arma3/10560386",
                              'mainserver_2': "https://www.battlemetrics.com/servers/arma3/10561000",
                              'testserver_1': "https://www.battlemetrics.com/servers/arma3/4789978",
                              'testserver_2': "https://www.battlemetrics.com/servers/arma3/9851037",
                              'eventserver': "https://www.battlemetrics.com/servers/arma3/9552734"}
    bot = None
    config_name = None

    def __init__(self, name: str, address: str, port: int):
        if self.bot is None:
            raise NeededClassAttributeNotSet('bot', self.__class__.__name__)
        if self.config_name is None:
            raise NeededClassAttributeNotSet('config_name', self.__class__.__name__)
        self.name = name
        self.address = address
        self.port = port
        self.encoding = 'utf-8'
        self.query_port = port + 1
        self.is_online = True
        self.battlemetrics_url = self.battle_metrics_mapping.get(self.name.casefold())
        self.starter_info_embed_message_id = None

    @property
    def query_full_address(self):
        if self.query_port is None:
            # TODO: custom error
            raise RuntimeError(f"query port for {self.name} community server is None")
        return (self.address, self.query_port)

    async def check_is_online(self):
        # TODO: Hardcode query_port to port +1
        log.debug("checking Server %s", self.name)
        try:
            check_data = await a2s.ainfo(self.query_full_address, timeout=self.timeout)
            self.is_online = True
        except asyncio.exceptions.TimeoutError:
            self.is_online = False

    @property
    def starter_info_channel(self):
        channel_id = COGS_CONFIG.retrieve(self.config_name, 'starter_info_channel_id', typus=int, direkt_fallback=None)
        if channel_id is None:
            raise NeededConfigValueMissing("starter_info_channel_id", self.config_name, self.__class__.__name__)
        return self.bot.sync_channel_from_id(channel_id)

    @property
    def starter_info_message(self):
        if self.starter_info_embed_message_id is None:
            return None
        return self.starter_info_channel.get_partial_message(self.starter_info_embed_message_id)

    async def redo_starter_info_message(self):
        pass

    async def to_embed(self):
        await self.check_is_online()
        if self.is_online is True:
            info = await self.get_info()
            password_needed = "YES 🔐" if info.password_protected is True else 'NO 🔓'
            embed_data = await self.bot.make_generic_embed(title=self.name.replace('_', ' '),
                                                           thumbnail="server",
                                                           description="✔️ Server is online",
                                                           fields=[self.bot.field_item(name="Server Address", value=str(self.address), inline=True),
                                                                   self.bot.field_item(name="Port", value=str(self.port), inline=True),
                                                                   self.bot.field_item(name="Teamspeak", value=f"38.65.5.151  {ZERO_WIDTH}  **OR**  {ZERO_WIDTH}  antistasi.armahosts.com"),
                                                                   self.bot.field_item(name="━━━━━━━━━━━━", value=ZERO_WIDTH, inline=False),
                                                                   self.bot.field_item(name="Game", value=info.game, inline=True),
                                                                   self.bot.field_item(name="Players", value=f"{info.player_count}/{info.max_players}", inline=True),
                                                                   self.bot.field_item(name="Ping", value=str(round(float(info.ping), ndigits=3)), inline=True),
                                                                   self.bot.field_item(name="Map", value=info.map_name, inline=True),
                                                                   self.bot.field_item(name="Password", value=f"{password_needed}", inline=True),
                                                                   self.bot.field_item(name='Battlemetrics', value="🔗 " + embed_hyperlink('link to Battlemetrics', self.battlemetrics_url), inline=True)],
                                                           author="armahosts",
                                                           footer="armahosts",
                                                           color="blue")
        else:
            embed_data = await self.bot.make_generic_embed(title=self.name.replace('_', ' '),
                                                           thumbnail="server",
                                                           description="❌ Server is **__NOT__** online",
                                                           fields=[self.bot.field_item(name="Server Address", value=str(self.address), inline=True),
                                                                   self.bot.field_item(name="Port", value=str(self.port), inline=True),
                                                                   self.bot.field_item(name="Teamspeak", value=f"38.65.5.151  {ZERO_WIDTH}  **OR**  {ZERO_WIDTH}  antistasi.armahosts.com"),
                                                                   self.bot.field_item(name='Battlemetrics', value="🔗 " + embed_hyperlink('link to Battlemetrics', self.battlemetrics_url), inline=True)],
                                                           author="armahosts",
                                                           footer="armahosts",
                                                           color="blue")
        return embed_data

    async def get_info(self):
        return await a2s.ainfo(self.query_full_address, encoding=self.encoding)

    async def get_rules(self):
        return await a2s.arules(self.query_full_address)

    async def get_players(self):
        return await a2s.aplayers(self.query_full_address, encoding=self.encoding)

    def __str__(self) -> str:
        return f"{self.name} = {self.address}:{self.port}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.address}, {self.port})"

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
