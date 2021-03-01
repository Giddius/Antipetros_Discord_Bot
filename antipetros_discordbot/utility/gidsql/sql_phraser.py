# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import logging

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# endregion[Imports]

__updated__ = '2020-11-03 03:34:53'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = logging.getLogger('gidsql')

glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

# endregion[Constants]


class GidSqlitePhraser:
    def __init__(self):
        self.template_folder = None
        self.created_scripts = {}


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
