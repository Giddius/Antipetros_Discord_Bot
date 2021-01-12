

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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pprint import pprint, pformat

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


# * PyQt5 Imports -->

from PyQt5.QtGui import QFont, QIcon, QBrush, QColor, QCursor, QPixmap, QStandardItem, QRegExpValidator
from PyQt5.QtCore import (Qt, QRect, QSize, QObject, QRegExp, QThread, QMetaObject, QCoreApplication,
                          QFileSystemWatcher, QPropertyAnimation, QAbstractTableModel, pyqtSlot, pyqtSignal)
from PyQt5.QtWidgets import (QMenu, QFrame, QLabel, QDialog, QLayout, QWidget, QWizard, QMenuBar, QSpinBox, QCheckBox, QComboBox,
                             QGroupBox, QLineEdit, QListView, QCompleter, QStatusBar, QTableView, QTabWidget, QDockWidget, QFileDialog,
                             QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QListWidget, QMainWindow, QMessageBox, QPushButton,
                             QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWizardPage, QApplication, QButtonGroup, QRadioButton,
                             QFontComboBox, QStackedWidget, QListWidgetItem, QTreeWidgetItem, QDialogButtonBox, QAbstractItemView,
                             QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator, QAction, QSystemTrayIcon, QInputDialog)


# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.dev_tools.gui.converted.Ui_create_cog_main_window import Ui_CreateCogMainWindow
from antipetros_discordbot.dev_tools.gui.commands.commands_model import CommandsListModel
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit, readit, readbin, writebin, writejson, loadjson, pickleit, get_pickled, work_in
import antipetros_discordbot
from antipetros_discordbot.dev_tools.gui.listener.listener_model import ListenerListModel
from antipetros_discordbot.dev_tools.gui.loops.new_loop_dialog import AddLoopDialog
from antipetros_discordbot.dev_tools.gui.loops.loops_model import LoopsListModel
from antipetros_discordbot.utility.named_tuples import NEW_COG_ITEM
from antipetros_discordbot.dev_tools.render_new_cog_file import create_cog_file
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

COGS_FOLDER = pathmaker(os.getenv('BASE_FOLDER'), 'cogs')

# endregion[Constants]


class CreateNewCogMainWindow(Ui_CreateCogMainWindow, QMainWindow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().setupUi(self)
        self.app = app
        self.package_basefolder = pathmaker(os.path.dirname(antipetros_discordbot.__file__))
        self.cogs_folder = self._find_cogs_folder()
        self.setup()
        self.actions()

    def setup(self):
        self.hide_disable_setup()
        self.category_setup()
        self.view_setup()

    def hide_disable_setup(self):
        self.custom_config_name_groupBox.setChecked(False)
        self.custom_config_name_lineEdit.setHidden(True)
        self.create_new_cog_file_pushButton.setEnabled(False)
        self.cog_exists_label.setHidden(True)

    def view_setup(self):
        self.commands_listView.setModel(CommandsListModel())
        self.listener_listView.setModel(ListenerListModel())
        self.loops_listView.setModel(LoopsListModel())

    def category_setup(self):
        self.cog_category_combo.clear()
        categories = [cat.replace('_cogs', '').title() for cat in self.cog_categories]
        self.cog_category_combo.addItems(categories)
        self.cog_category_combo.addItem('New Category...')

    def actions(self):
        self.add_command_pushButton.pressed.connect(self.commands_listView.model().add_command)
        self.add_listener_pushButton.pressed.connect(self.listener_listView.model().add_listener)
        self.add_loop_pushButton.pressed.connect(self.open_add_loop_dialog)
        self.cog_category_combo.currentTextChanged.connect(self.add_new_category)
        self.custom_config_name_groupBox.toggled.connect(self.show_custom_config_name_line_edit)
        self.cog_name_lineedit.textChanged.connect(self.check_existing_name)
        self.create_new_cog_file_pushButton.pressed.connect(self.create_cog)

    def check_existing_name(self, text):
        if any(text.casefold() == item.replace('_cog', '').casefold() for item in self.existing_cogs(typus='purename')):
            self.create_new_cog_file_pushButton.setEnabled(False)
            self.cog_exists_label.setHidden(False)
        elif text != '':
            self.create_new_cog_file_pushButton.setEnabled(True)
            self.cog_exists_label.setHidden(True)
        else:
            self.create_new_cog_file_pushButton.setEnabled(False)

    def show_custom_config_name_line_edit(self):
        if self.custom_config_name_groupBox.isChecked() is True:
            self.custom_config_name_lineEdit.setHidden(False)
            self.custom_config_name_lineEdit.setEnabled(True)
        else:
            self.custom_config_name_lineEdit.setEnabled(False)
            self.custom_config_name_lineEdit.setHidden(True)

    def open_add_loop_dialog(self):
        dialog = AddLoopDialog(self.loops_listView.model().items)
        dialog.dialog_accepted.connect(self.loops_listView.model().add_loop)
        dialog.exec()

    def add_new_category(self, text):
        if text != 'New Category...':
            return
        _name, _ok = QInputDialog.getText(None, "Add New Category", "New Category Name", QLineEdit.Normal)
        if _ok:
            foldername = _name.replace(' ', '_').lower()
            if not foldername.endswith('_cogs'):
                foldername = foldername + '_cogs'
            path = pathmaker(self.cogs_folder, foldername)
            if os.path.isdir(path) is False:
                os.makedirs(path)
                writeit(pathmaker(path, '__init__.py'), '')
        self.category_setup()

    @property
    def cog_categories(self):
        _out = []
        for item in os.scandir(self.cogs_folder):
            if os.path.isdir(item.path) and not item.name.startswith('__'):
                _out.append(item.name)
        return _out

    def existing_cogs(self, typus='raw'):
        _out = []
        for dirname, folderlist, filelist in os.walk(self.cogs_folder):
            for file in filelist:
                if file.endswith('_cog.py'):
                    _out.append(file)
        if typus == 'raw':
            return _out

        elif typus == 'purename':
            return list(map(lambda x: x.replace('.py', ''), _out))

        elif typus == 'classname':
            return list(map(lambda x: x.replace('.py', '').replace('_', ' ').title().replace(' ', ''), _out))

    def _find_cogs_folder(self):
        for dirname, folderlist, filelist in os.walk(self.package_basefolder):
            for folder in folderlist:
                if folder == 'cogs':
                    return pathmaker(dirname, folder)

    def print_cogs(self):
        pprint(self.existing_cogs())
        print('##################')
        pprint(self.existing_cogs('purename'))
        print('##################')
        pprint(self.existing_cogs('classname'))

    def get_all_com_attr(self):
        _out = {}
        if self.comattr_hidden_checkBox.isChecked():
            _out = [('hidden', True)]
        return _out

    def create_cog(self):
        name = self.cog_name_lineedit.text().title().replace('_', '')
        absoute_path = pathmaker(COGS_FOLDER, self.cog_category_combo.currentText().lower() + '_cogs', self.cog_name_lineedit.text() + '_cog.py')
        import_location = self.cog_category_combo.currentText().lower() + '_cogs.' + self.cog_name_lineedit.text() + '_cog'
        config_name = self.cog_name_lineedit.text() if self.custom_config_name_groupBox.isChecked() is False else self.custom_config_name_lineEdit.text()
        if config_name == '':
            config_name = self.cog_name_lineedit.text()
        all_com_attr = self.get_all_com_attr()
        all_loops = self.loops_listView.model().items
        all_listeners = self.listener_listView.model().items
        all_commands = self.commands_listView.model().items
        extra_imports = []
        code = ''
        cog_item = NEW_COG_ITEM(name, absoute_path, import_location, config_name, all_com_attr, all_loops, all_listeners, all_commands, extra_imports, code)
        create_cog_file(cog_item)
        self.app.quit()


def new_cog_ui():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    main_window = CreateNewCogMainWindow(app)
    main_window.show()

    sys.exit(app.exec_())


# region[Main_Exec]
if __name__ == '__main__':
    new_cog_ui()

# endregion[Main_Exec]
