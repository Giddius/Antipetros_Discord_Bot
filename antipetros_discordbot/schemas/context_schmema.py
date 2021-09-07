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
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty
from antipetros_discordbot.schemas.extra_schemas import RequiredFileSchema, RequiredFolderSchema, ListenerSchema
import gidlogger as glog

from inspect import getdoc
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


class AntiPetrosBaseContextSchema(Schema):
    bot = fields.Nested("AntiPetrosBotSchema")
    cog = fields.Nested("AntiPetrosBaseCogSchema")
    message = fields.String()
    channel = fields.String()
    guild = fields.String()

    class Meta:
        ordered = True
        additional = ('valid',
                      "prefix")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
