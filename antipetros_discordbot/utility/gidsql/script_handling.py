# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import logging
from pprint import pformat

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import readit, writeit, pathmaker

# endregion [Imports]

__updated__ = '2020-11-22 15:00:32'


# region [Logging]
log = logging.getLogger('gidsql')

glog.import_notification(log, __name__)

# endregion [Logging]


class GidSqliteScriptProvider:
    def __init__(self, script_folder):
        self.script_folder = script_folder
        self.setup_prefix = 'setup'

    @property
    def scripts(self):
        _out_dict = {}
        for _file in os.scandir(self.script_folder):
            if os.path.isfile(_file.path) is True and _file.name.endswith('.sql') and not _file.name.startswith(self.setup_prefix):
                _bare_name = _file.name.split('.')[0]
                _out_dict[_bare_name] = _file.path
        return _out_dict

    @property
    def setup_scripts(self):
        # sourcery skip: inline-immediately-returned-variable, list-comprehension
        setup_scripts = []
        for _file in os.scandir(self.script_folder):
            if os.path.isfile(_file.path) is True and _file.name.endswith('.sql') and _file.name.startswith(self.setup_prefix):
                setup_scripts.append(readit(_file.path))
        return setup_scripts

    def __getitem__(self, key):
        _file = self.scripts.get(key, None)
        if _file:
            return readit(_file)

    def __contains__(self, key):
        return key in self.scripts

    def __len__(self):
        return len(self.scripts)

    def __setitem__(self, key, value):
        _name = key + '.sql'
        _path = pathmaker(self.script_folder, _name)
        writeit(_path, value)

    def get(self, key, default=None):
        _out = self[key]
        if _out is None:
            _out = default

        return _out

    def __repr__(self):
        return f"{self.__class__.__name__}({self.script_folder})"

    def __str__(self):
        _out = []
        for _file in os.scandir(self.script_folder):
            if _file.name.endswith('.sql'):
                _out.append(_file.name)
        return pformat(_out)


if __name__ == '__main__':
    pass
