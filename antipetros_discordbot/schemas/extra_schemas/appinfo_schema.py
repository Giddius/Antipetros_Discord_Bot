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


class UserSchema(Schema):
    class Meta:
        additional = ('id', 'display_name', 'name')


class AppInfoSchema(Schema):
    owner = fields.Nested(UserSchema)
    icon = fields.Function(lambda obj: obj.icon_url._url)

    class Meta:
        additional = ('id', 'name', 'description', 'bot_public', 'bot_require_code_grant', 'summary')


    # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
