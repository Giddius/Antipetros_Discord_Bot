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


class RequiredFileSchema(Schema):
    file_type = fields.String()

    class Meta:
        additional = ('path', 'name', 'default_content', 'dir_path',)


class RequiredFolderSchema(Schema):
    path = fields.String()
    name = fields.String()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
