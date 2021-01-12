

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
                             QCommandLinkButton, QAbstractScrollArea, QGraphicsOpacityEffect, QTreeWidgetItemIterator, QAction, QSystemTrayIcon)


# * Gid Imports -->

import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writeit, readit, readbin, writebin, writejson, loadjson, pickleit, get_pickled, work_in

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

class BaseCogPartsModel(QAbstractTableModel):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.header = ['name']

    def data(self, index, role):
        try:
            if not index.isValid():
                return None
            elif role in [Qt.DisplayRole, Qt.EditRole]:
                return self.content_display(index)
            elif role == Qt.ToolTipRole:
                return self.content_tooltip(index)
            elif role == Qt.BackgroundRole:
                return self.content_background(index)
            elif role == Qt.ForegroundRole:
                return self.content_fontcolor(index)
            elif role == Qt.DecorationRole:
                return self.content_icon(index)
            elif role == Qt.StatusTipRole:
                return self.content_status_tip(index)
            elif role == Qt.SizeHintRole:
                return self.content_size_hint(index)
        except KeyError as error:
            log.error("%s with row index: %s and column index: %s for role: %s", error, index.row(), index.column(), role)

    def content_size_hint(self, index):
        pass

    def content_icon(self, index):
        pass

    def content_fontcolor(self, index):
        pass

    def content_background(self, index):
        pass

    def content_tooltip(self, index):
        pass

    def content_display(self, index):
        return self.items[index.row()].name

    def content_status_tip(self, index):
        pass

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def rowCount(self, index):
        return len(self.items)

    def columnCount(self, parent):
        return len(self.header)

    def flags(self, index) -> Qt.ItemFlags:
        return super().flags(index)

    def remove(self, index):
        self.layoutAboutToBeChanged.emit()
        _ = self.items.pop(index.row())
        self.layoutChanged.emit()

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
