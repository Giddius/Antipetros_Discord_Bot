

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
from antipetros_discordbot.utility.named_tuples import NEW_COMMAND_ITEM, NEW_LOOP_ITEM
from antipetros_discordbot.dev_tools.gui.converted.Ui_new_loop_dialog import Ui_AddLoopDialog
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

class AddLoopDialog(Ui_AddLoopDialog, QDialog):
    dialog_accepted = pyqtSignal(str, dict)

    def __init__(self, existing_loops, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().setupUi(self)
        self.existing_loops = existing_loops
        self.setup()
        self.actions()

    def setup(self):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.loop_name_exists_label.setHidden(True)

    def actions(self):
        self.loop_name_lineEdit.textChanged.connect(self.check_existing_name)
        self.buttonBox.accepted.connect(self.check_emit)
        self.count_none_checkBox.toggled.connect(self.switch_count_select)

    def check_existing_name(self, text):
        if any(text.casefold() == item.name.casefold() for item in self.existing_loops):
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            self.loop_name_exists_label.setHidden(False)
        elif text != '':
            self.loop_name_exists_label.setHidden(True)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.loop_name_exists_label.setHidden(True)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def switch_count_select(self):
        if self.count_none_checkBox.isChecked() is False:
            self.count_spinBox.setEnabled(True)
        else:
            self.count_spinBox.setEnabled(False)

    def check_emit(self):
        name = self.loop_name_lineEdit.text()
        attributes = {"hours": self.hours_spinBox.value(),
                      'minutes': self.minutes_spinBox.value(),
                      'seconds': self.minutes_spinBox.value(),
                      'count': None if self.count_none_checkBox.isChecked() else self.count_spinBox.value(),
                      'loop': None if self.loop_comboBox.currentText() == 'None' else self.loop_comboBox.currentText()}
        self.dialog_accepted.emit(name, attributes)
        self.accept()


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
