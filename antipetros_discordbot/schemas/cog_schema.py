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
from antipetros_discordbot.schemas.command_schema import AntiPetrosBaseCommandSchema
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


class AntiPetrosBaseCogSchema(Schema):
    name = fields.String()
    required_folder = fields.Nested(RequiredFolderSchema())
    required_files = fields.Nested(RequiredFileSchema())
    all_listeners = fields.List(fields.Nested(ListenerSchema()))
    meta_status = fields.Method("split_meta_status")
    github_link = fields.Url()
    github_wiki_link = fields.Url()
    loops = fields.Method("handle_loops")

    class Meta:
        ordered = True
        additional = ('config_name',
                      'public',
                      'description',
                      'long_description',
                      'extra_info',
                      'qualified_name',
                      'required_config_data',
                      'short_doc',
                      'brief',
                      'docstring')

    def split_meta_status(self, obj):
        meta_status = str(obj.meta_status)
        clean_meta_status = meta_status.split('.')[-1]
        return list(map(lambda x: x.strip(), clean_meta_status.split('|')))

    def handle_loops(self, obj):
        loop_data = obj.get_loops()
        _out = {}
        for name, loop in loop_data.items():
            _out[name] = {"docstring": getdoc(loop.coro),
                          "loop_interval": alt_seconds_to_pretty((loop.seconds + (loop.minutes * 60.0) + (loop.hours * 3600.0)))}
        return _out


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
