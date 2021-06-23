"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


import gidlogger as glog
from marshmallow import Schema, fields, post_dump, pre_dump

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


class AntiPetrosBaseCommandSchema(Schema):
    gif = fields.Raw()
    allowed_channels = fields.List(fields.Str())
    allowed_roles = fields.List(fields.Str())
    allowed_in_dms = fields.Bool()
    allowed_members = fields.List(fields.Str())
    parent = fields.Nested(lambda: AntiPetrosBaseCommandSchema(), default=None)
    categories = fields.List(fields.Nested('CommandCategorySchema', exclude=('commands',)))

    class Meta:
        additional = ('best_alias',
                      '_old_data',
                      'docstring',
                      'description',
                      'brief',
                      'short_doc',
                      'usage',
                      'signature',
                      'example',
                      'enabled',
                      'hidden',
                      'aliases',
                      'name',
                      'github_link',
                      'github_wiki_link',
                      'cog_name')

    @post_dump
    def command_category_to_dict(self, in_data, **kwargs):
        in_data['categories'] = {item.get('name'): item for item in in_data['categories']}
        return in_data


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
