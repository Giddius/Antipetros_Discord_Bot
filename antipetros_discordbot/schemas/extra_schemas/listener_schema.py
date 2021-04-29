"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata



from marshmallow import Schema, fields
import gidlogger as glog


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


class ListenerSchema(Schema):
    name = fields.Str()
    event = fields.Str()
    github_link = fields.Str()
    file = fields.Str()
    code = fields.Str()
    description = fields.Str()

    # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
