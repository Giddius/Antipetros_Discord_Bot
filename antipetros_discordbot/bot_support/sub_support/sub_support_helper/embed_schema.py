"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime, timezone

# * Third Party Imports --------------------------------------------------------------------------------->
from pytz import timezone
from marshmallow import Schema, fields

# * Gid Imports ----------------------------------------------------------------------------------------->
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


class EmbedAuthorSchema(Schema):
    name = fields.String()
    url = fields.String()
    icon_url = fields.String()


class EmbedFooterSchema(Schema):
    text = fields.String()
    icon_url = fields.String()


class EmbedFieldSchema(Schema):
    name = fields.String(required=True)
    value = fields.String(required=True)
    inline = fields.Boolean(default=False)


class EmbedPrototypeSchema(Schema):
    title = fields.String(required=True)
    description = fields.String()
    color = fields.String(missing='green')
    thumbnail = fields.String()
    image = fields.String()
    timestamp = fields.DateTime(missing=datetime.now(tz=timezone("Europe/Berlin")))
    footer = fields.Nested(EmbedFooterSchema, default=None)
    author = fields.Nested(EmbedAuthorSchema, default=None)
    embed_fields = fields.List(fields.Nested(EmbedFieldSchema))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]