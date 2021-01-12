

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

from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit, readit, readbin, writebin, writejson, loadjson, pickleit, get_pickled, work_in
from antipetros_discordbot.dev_tools.gui.models.base_model import BaseCogPartsModel
from antipetros_discordbot.utility.named_tuples import NEW_COMMAND_ITEM, NEW_LISTENER_ITEM, NEW_LOOP_ITEM, NEW_COG_ITEM
from antipetros_discordbot.utility.misc import EVENTS
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]


# endregion[Constants]

class ListenerListModel(BaseCogPartsModel):
    listener_item = NEW_LISTENER_ITEM

    def add_listener(self):
        _name, _ok = QInputDialog.getText(None, "Add New Command", "New Command Name", QLineEdit.Normal)
        if _ok:
            name = _name.replace(' ', '_').lower()
            if all(name != item.name for item in self.items):
                _event_name, _ok = QInputDialog.getItem(None, 'Listener Event', 'Select Listener Event', EVENTS, 0, False)
                if _ok:
                    self.layoutAboutToBeChanged.emit()
                    self.items.append(self.listener_item(name, _event_name, ''))
                    self.layoutChanged.emit()
            else:
                QMessageBox.critical(None, 'Command does already exist'.title(), 'please choose another name'.title(), QMessageBox.Ok)

    def content_tooltip(self, index):
        return self.items[index.row()].event_name

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
