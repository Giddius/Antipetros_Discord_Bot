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
from antipetros_discordbot.schemas.extra_schemas import RequiredFileSchema, RequiredFolderSchema, ListenerSchema
from antipetros_discordbot.schemas.command_schema import AntiPetrosBaseCommandSchema
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


class AntiPetrosBaseCogSchema(Schema):
    required_folder = fields.Nested(RequiredFolderSchema())
    required_files = fields.Nested(RequiredFileSchema())
    all_listeners = fields.List(fields.Nested(ListenerSchema()))
    all_commands = fields.List(fields.Nested(AntiPetrosBaseCommandSchema()))

    class Meta:
        additional = ('name', 'config_name', 'public', 'description', 'long_description', 'extra_info', 'qualified_name', 'required_config_data', 'short_doc', 'brief', 'github_link', 'github_wiki_link')

    def cast_listeners(self, obj):
        return {listener_name: listener_method.__name__ for listener_name, listener_method in obj.all_listeners}


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
