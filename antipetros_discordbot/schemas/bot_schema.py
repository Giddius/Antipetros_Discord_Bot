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
from antipetros_discordbot.schemas.cog_schema import AntiPetrosBaseCogSchema
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


class AntiPetrosBotSchema(Schema):
    owner_ids = fields.List(fields.Integer())
    version = fields.String()
    github_url = fields.Url()
    github_wiki_url = fields.Url()
    portrait_url = fields.Url()
    antistasi_invite_url = fields.Url()
    intents = fields.Function(lambda obj: [{"name": k, "value": v} for k, v in iter(obj.intents)])

    class Meta:
        additional = ('name',
                      'id',
                      'display_name',
                      'description'
                      'case_insensitive',
                      'strip_after_prefix',
                      'antistasi_invite_url',
                      'command_amount',
                      'cog_amount',
                      'creator_id',
                      'antistasi_guild_id',
                      'brief',
                      'short_doc',
                      'long_description',
                      'extra_info',
                      'app_name',
                      'author_name')


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
