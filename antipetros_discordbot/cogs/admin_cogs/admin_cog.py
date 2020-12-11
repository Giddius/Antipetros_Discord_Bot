

# region [Imports]

# * Standard Library Imports -->

import asyncio
import gc
import logging
import os
import re
import sys
import json
import lzma
import time
import queue
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# * Third Party Imports -->

from discord.ext import commands, tasks
from discord import DiscordException
import discord
from fuzzywuzzy import process as fuzzprocess
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process


# * PyQt5 Imports -->

# from PyQt5.QtGui import QFont, QIcon, QBrush, QColor, QCursor, QPixmap, QStandardItem, QRegExpValidator
# from PyQt5.QtCore import (Qt, QRect, QSize, QObject, QRegExp, QThread, QMetaObject, QCoreApplication,
#                           QFileSystemWatcher, QPropertyAnimation, QAbstractTableModel, pyqtSlot, pyqtSignal)
# from PyQt5.QtWidgets import (QMenu, QFrame, QLabel, QDialog, QLayout, QWidget, QWizard, QMenuBar, QSpinBox, QCheckBox, QComboBox,
#                              QGroupBox, QLineEdit, QListView, QCompleter, QStatusBar, QTableView, QTabWidget, QDockWidget, QFileDialog,
#                              QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QListWidget, QMainWindow, QMessageBox, QPushButton,
#                              QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWizardPage, QApplication, QButtonGroup, QRadioButton,
#                              QFontComboBox, QStackedWidget, QListWidgetItem, QTreeWidgetItem, QDialogButtonBox, QAbstractItemView,
#                              QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator, QAction, QSystemTrayIcon)


# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.misc import seconds_to_pretty
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class Administration(commands.Cog):
    # region [ClassAttributes]

    config_name = 'admin'

    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.all_configs = [BASE_CONFIG, COGS_CONFIG]
        self.config_dir = APPDATA['config']
        if self.bot.is_debug:
            self.save_commands()
        glog.class_init_notification(log, self)

    def save_commands(self):
        command_json_file = r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\docs\commands.json"
        command_json = loadjson(command_json_file)
        command_json[str(self)] = {'file_path': pathmaker(os.path.abspath(__file__)),
                                   'description': __doc__,
                                   'commands': {(com.name + ' ' + com.signature).replace('<ctx>', '').replace('  ', ' ').strip(): com.help for com in self.get_commands()}}
        writejson(command_json, command_json_file, indent=4)
        log.debug("commands for %s saved to %s", self, command_json_file)

# endregion[Init]

# region [Properties]

    @ property
    def allowed_dm_invoker_ids(self):
        return set(map(int, COGS_CONFIG.getlist(self.config_name, 'allowed_dm_ids')))

    @ property
    def allowed_channels(self):
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

# endregion[Properties]

    @ commands.Cog.listener(name='on_ready')
    async def extra_cog_setup(self):
        log.info(f"{self} Cog ----> nothing to set up")

    async def get_available_configs(self):  # sourcery skip: dict-comprehension
        found_configs = {}
        for _file in os.scandir(self.config_dir):
            if 'config' in _file.name and os.path.splitext(_file.name)[1] in ['.ini', '.json', '.yaml', '.toml']:
                found_configs[os.path.splitext(_file.name)[0]] = _file.name
        return found_configs

    async def config_file_to_discord_file(self, config_name):
        config_path = pathmaker(self.config_dir, config_name) if '/' not in config_name else config_name
        return discord.File(config_path, config_name)

    async def match_config_name(self, config_name_input):
        available_configs = await self.get_available_configs()
        _result = fuzzprocess.extractOne(config_name_input, choices=available_configs.keys(), score_cutoff=80)
        if _result is None:
            return None
        else:
            return pathmaker(self.config_dir, available_configs[_result[0]])

    @ commands.command(name="reload_all")
    @ commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def reload_all_ext(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        _extensions_list = []
        BASE_CONFIG.read()
        COGS_CONFIG.read()
        reloaded_extensions = ''
        _base_location = BASE_CONFIG.get('general_settings', 'cogs_location')
        for _extension in BASE_CONFIG.options('extensions'):
            if BASE_CONFIG.getboolean('extensions', _extension) is True:
                _location = _base_location + '.' + _extension
                try:
                    self.bot.unload_extension(_location)
                    self.bot.load_extension(_location)
                    log.debug('Extension Cog "%s" was successfully reloaded from "%s"', _extension.split('.')[-1], _location)
                    reloaded_extensions += f"> __'{_extension}'__ was **SUCCESSFULLY** reloaded!\n\n"
                except DiscordException as error:
                    log.error(error)

        _delete_time = 5 if self.bot.is_debug is True else 30
        # TODO: make as embed
        await ctx.send(f"**successfully reloaded the following extensions:**\n{reloaded_extensions}", delete_after=_delete_time)
        await ctx.message.delete(delay=float(_delete_time - (_delete_time // 2)))

    @ commands.command(name='die', aliases=['go_away', 'turn_of', 'shutdown', 'exit', 'close'])
    @ commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def shutdown(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        log.debug('shutdown command received from "%s"', ctx.author.name)
        started_at = self.bot.start_time.strftime(self.bot.std_date_time_format)
        embed = await self.bot.make_basic_embed(title='cya!', text='AntiPetros is shutting down.', symbol='shutdown', was_online_since=started_at, commands_executed=str(self.bot.commands_executed))
        embed.set_image(url='https://media.discordapp.net/attachments/449481990513754114/785601325329023006/2d1ca5fea58e65277ac5c18788b21d03.gif')
        await ctx.send(embed=embed)
        await self.bot.logout()

    @ commands.command(name='list_configs')
    @ commands.dm_only()
    async def list_configs(self, ctx):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            _embed = discord.Embed(title="Anti Petros Report")
            await add_to_embed_listfield(_embed, 'Available Configs', available_configs.keys(), prefix='-')
            # TODO: make as embed
            await ctx.send(embed=_embed)

            log.info("config list send to '%s'", ctx.author.name)

    @ commands.command(name='send_config')
    @ commands.dm_only()
    async def config_request(self, ctx, config_name='all'):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            requested_configs = []
            if config_name.casefold() == 'all':
                requested_configs = [conf_file_name for key, conf_file_name in available_configs.items()]

            else:
                _req_config_path = await self.match_config_name(config_name)
                requested_configs.append(os.path.basename(_req_config_path))

            if requested_configs == []:
                # TODO: make as embed
                await ctx.send(f'I was **NOT** able to find a config named `{config_name}`!\nTry again with `all` as argument, or request the available configs with the command `list_configs`')
            else:
                for req_config in requested_configs:
                    _msg = f"Here is the file for the requested config `{req_config}`"
                    _file = await self.config_file_to_discord_file(req_config)
                    # TODO: make as embed
                    await ctx.send(_msg, file=_file)
                log.info("requested configs (%s) send to %s", ", ".join(requested_configs), ctx.author.name)

    @ commands.command(name='overwrite_config')
    @ commands.dm_only()
    async def overwrite_config_from_file(self, ctx, config_name):
        if ctx.author.id not in self.allowed_dm_invoker_ids:
            return
        if len(ctx.message.attachments) > 1:
            # TODO: make as embed
            await ctx.send('please only send a single file with the command')
            return
        _file = ctx.message.attachments[0]
        _config_path = await self.match_config_name(config_name)
        if _config_path is None:
            # TODO: make as embed
            await ctx.send(f'could not find a config that fuzzy matches `{config_name}`')
        else:
            await _file.save(_config_path)
            for cfg in self.all_configs:
                cfg.read()
                # TODO: make as embed
            await ctx.send(f'saved your file as `{os.path.basename(_config_path)}`.\n\n_You may have to reload the Cogs or restart the bot for it to take effect!_')

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def add_to_blacklist(self, ctx, user_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        user = await self.bot.fetch_user(user_id)
        if user is None:
            # TODO: make as embed
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        if user.bot is True:
            # TODO: make as embed
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        current_blacklist = self.bot.blacklist_user
        current_blacklist.append(user_id)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            # TODO: make as embed
            await user.send(f"***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.notify_contact_member}__** per DM!")
        else:
            # TODO: make as embed
            await user.send(f"You have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.notify_contact_member}__** per DM!")
            # TODO: make as embed
        await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!\n\nI have also notified him by DM of this fact!")

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def remove_from_blacklist(self, ctx, user_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        user = await self.bot.fetch_user(user_id)
        if user is None:
            # TODO: make as embed
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        current_blacklist = self.bot.blacklist_user
        if user.id not in current_blacklist:
            # TODO: make as embed
            await ctx.send(f"User '{user.name}' with User_id '{user.id}' is currently **__NOT__** in my ***Blacklist***\n and can therefor not be removed from the ***Blacklist***!")
            return

        for index, item in enumerate(current_blacklist):
            if item == user_id:
                to_delete_index = index
                break
        current_blacklist.pop(to_delete_index)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            # TODO: make as embed
            await user.send("***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
        else:
            # TODO: make as embed
            await user.send("You have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
            # TODO: make as embed
        await ctx.send(f"User '{user.name}' with User_id '{user.id}' was removed from my Blacklist.\n\nHe is now able again, to invoke my commands!")

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def tell_uptime(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        now_time = datetime.utcnow()
        delta_time = now_time - self.bot.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n\t\t| {str(seconds_to_pretty(seconds))}")
        log.info(f"reported uptime to '{ctx.author.name}'")

    @ commands.command()
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def delete_msg(self, ctx, msg_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(Administration(bot))
