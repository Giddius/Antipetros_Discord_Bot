"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Callable
from datetime import datetime
from collections import UserDict

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]


# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
# * Local Imports --------------------------------------------------------------------------------------->
# * Local Imports -->
from antipetros_discordbot.utility.misc import date_today

# endregion[Constants]


class CommandStatDict(UserDict):
    overall_data_file = pathmaker(APPDATA['stats'], "overall_invoked_stats.json")

    def __init__(self, file: str, default_content_function: Callable):
        self.file = pathmaker(file)
        super().__init__({})
        self.default_content_function = default_content_function
        self.default_content = None
        self.last_initialized = None
        self.load_data()

    @property
    def is_empty(self):
        return self.data == {}

    @property
    def sum_data(self):
        _out = {'overall': {'successful': sum(value.get('successful') for key, value in self.data['overall'].items()),
                            'unsuccessful': sum(value.get('unsuccessful') for key, value in self.data['overall'].items())}}

        for date, value in self.data.items():
            if date != 'overall':
                _out[date] = {'successful': sum(value.get('successful') for key, value in self.data[date].items()),
                              'unsuccessful': sum(value.get('unsuccessful') for key, value in self.data[date].items())}
        return _out

    def initialize_data(self):
        self.default_content = list(set(self.default_content_function()))
        if 'overall' not in self.data:
            self.data['overall'] = {}
        if date_today() not in self.data:
            self.data[date_today()] = {}
        for item in self.default_content:
            if item not in self.data['overall']:
                self.data['overall'][item] = {'successful': 0, 'unsuccessful': 0}
            if item not in self.data[date_today()]:
                self.data[date_today()][item] = {'successful': 0, 'unsuccessful': 0}
        self.last_initialized = datetime.utcnow()

    def add_tick(self, key, unsuccessful=False):
        if key is None or key == 'None':
            return
        if self.last_initialized.day != datetime.utcnow().day or date_today() not in self.data:
            self.save_data()
            self.initialize_data()

        typus = 'unsuccessful' if unsuccessful is True else "successful"
        if key not in self.data['overall']:
            self.data['overall'][key] = {'successful': 0, 'unsuccessful': 0}
        self.data['overall'][key][typus] += 1
        if key not in self.data[date_today()]:
            self.data[date_today()][key] = {'successful': 0, 'unsuccessful': 0}
        self.data[date_today()][key][typus] += 1

    def load_data(self):
        if os.path.isfile(self.file) is False:
            self.initialize_data()
            self.save_data()
        self.data = loadjson(self.file)
        self.initialize_data()

    def save_data(self):
        writejson(self.data, self.file)

    def save_overall(self):
        writejson(self.sum_data, self.overall_data_file)


# region[Main_Exec]

if __name__ == '__main__':
    pass
# endregion[Main_Exec]
