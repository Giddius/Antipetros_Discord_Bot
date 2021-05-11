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
    private_channels = fields.List(fields.String())
    cogs = fields.Dict(keys=fields.String(), values=fields.Nested(AntiPetrosBaseCogSchema()))
    github_url = fields.Url()
    github_wiki_url = fields.Url()
    portrait_url = fields.Url()
    antistasi_invite_url = fields.Url()

    class Meta:
        additional = ('name',
                      'id',
                      'display_name',
                      'description'
                      'non_mention_prefixes',
                      'case_insensitive',
                      'latency',
                      'strip_after_prefix',
                      'start_time',
                      'uptime',
                      'uptime_pretty',
                      'antistasi_invite_url',
                      'self_bot',
                      'command_amount',
                      'cog_amount',
                      'creator_id',
                      'antistasi_guild_id',
                      'brief',
                      'short_doc',
                      'long_description',
                      'extra_info')


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
