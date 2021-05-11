"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import sys
import asyncio
import unicodedata
from pprint import pprint, pformat
from typing import Any, get_type_hints, get_args, _GenericAlias
from inspect import getdoc
from functools import singledispatchmethod
import inspect
import re
# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord

# import requests

# import pyperclip

# import matplotlib.pyplot as plt

# from bs4 import BeautifulSoup

# from dotenv import load_dotenv

# from discord import Embed, File

from discord.ext import commands, tasks, flags, ipc

# from github import Github, GithubException

# from jinja2 import BaseLoader, Environment

# from natsort import natsorted

# from fuzzywuzzy import fuzz, process


# * Gid Imports ------------------------------------------------------------------------------------------------------------------------------------------------->

import gidlogger as glog
from copy import copy, deepcopy
from icecream import ic
# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.engine.replacements.helper import JsonMetaDataProvider, JsonAliasProvider, SourceCodeProvider
from antipetros_discordbot.utility.checks import dynamic_enabled_checker
from antipetros_discordbot.schemas import AntiPetrosBaseCommandSchema
from antipetros_discordbot.engine.replacements.command_replacements.command_category import CommandCategory
from antipetros_discordbot.utility.gidtools_functions import pathmaker
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AntiPetrosBaseCommand(commands.Command):
    is_group = False
    meta_data_provider = JsonMetaDataProvider(pathmaker(APPDATA['documentation'], 'command_meta_data.json'))
    alias_data_provider = JsonAliasProvider()
    source_code_data_provider = SourceCodeProvider()
    bot_mention_placeholder = '@BOTMENTION'
    # args_regex = re.compile(r"args\:\n(?P<args_values>.*?)(?:\n\s*example:.*)?$", re.IGNORECASE | re.DOTALL)
    args_regex = re.compile(r"(?P<description>.*?)(?P<args>args\:.*?(?=example\:)?)?(?P<example>example\:.*)?$", re.IGNORECASE | re.DOTALL)
    schema = AntiPetrosBaseCommandSchema()

    def __init__(self, func, **kwargs):
        self.name = func.__name__ if kwargs.get("name") is None else kwargs.get("name")
        self.extra_aliases = kwargs.pop("aliases", None)
        self.data_getters = {'meta_data': self.meta_data_provider.get_auto_provider(self),
                             'alias': self.alias_data_provider.get_auto_provider(self),
                             'source_code': self.source_code_data_provider.get_auto_provider(self)}

        self.data_setters = {'meta_data': self.meta_data_provider.set_auto_provider(self),
                             'alias': self.alias_data_provider.set_auto_provider(self)}

        self.data_removers = {'alias': self.alias_data_provider.remove_auto_provider(self)}
        self._old_data = {'help': None,
                          'brief': None,
                          'description': None,
                          'short_doc': None,
                          'usage': None,
                          'signature': None}
        self.categories = []
        super().__init__(func, **kwargs)
        self.handle_category_kwargs(kwargs.get('categories', []))
        self.module_object = sys.modules[func.__module__]
        self.data_setters['meta_data']("docstring", self.docstring)

    @property
    def bot(self):
        return self.cog.bot

    @singledispatchmethod
    def handle_category_kwargs(self, categories: Any):
        pass

    @handle_category_kwargs.register
    def handle_category_kwargs_list(self, categories: list):
        for category in categories:
            category.add_command(self)

    @handle_category_kwargs.register(type(CommandCategory))
    def handle_category_kwargs_single(self, categories):
        categories.add_command(self)

    async def set_alias(self, new_alias: str):
        self.data_setters['alias'](new_alias)

    async def get_source_code_image(self):
        return await asyncio.to_thread(self.data_getters['source_code'], typus='image')

    @property
    def enabled(self):
        return dynamic_enabled_checker(self)

    @enabled.setter
    def enabled(self, value):
        pass

    @property
    def docstring(self):
        return getdoc(self.callback)

    @property
    def aliases(self):
        aliases = self.data_getters['alias'](extra_aliases=self.extra_aliases)
        self.alias = aliases
        return aliases

    @aliases.setter
    def aliases(self, value):
        if isinstance(value, list):
            for alias in value:
                self.data_setters['alias'](alias)
        elif isinstance(value, str):
            self.data_setters['alias'](value)

    @property
    def long_description(self):
        _help = self.data_getters['meta_data']('long_description', 'NA')

        return inspect.cleandoc(_help)

    @long_description.setter
    def long_description(self, value):
        self._old_data['long_description'] = value

    @property
    def extra_info(self):
        extra_info = self.data_getters['meta_data']('extra_info', None)
        return extra_info

    @extra_info.setter
    def extra_info(self, value):
        self.data_setters['meta_data']('extra_info', value)

    @property
    def brief(self):
        brief = self.data_getters['meta_data']('brief')
        if brief is None:
            brief = self.data_getters['meta_data']('short_doc')
        if brief is None:
            brief = self._old_data.get('brief')
        return brief

    @brief.setter
    def brief(self, value):
        self._old_data['brief'] = value

    @property
    def description(self):
        description = self.data_getters['meta_data']('description')
        if description in ['', None, 'NA']:
            description = self.docstring
        if not description:
            description = 'NA'
        return description

    @description.setter
    def description(self, value):
        self._old_data['description'] = value

    @property
    def short_doc(self):
        short_doc = self.data_getters['meta_data']('short_doc', 'NA')
        return short_doc

    @short_doc.setter
    def short_doc(self, value):
        self._old_data['short_doc'] = value

    @property
    def usage(self):
        usage = {}

        # for key, value in self.callback.__annotations__.items():
        #     if key not in ['self', 'ctx']:

        #         if value is str:
        #             usage[f"<{key}>"] = "Text that needs to be put in quotes if it contains spaces."
        #         elif value is int:
        #             usage[f"<{key}>"] = "A number"
        #         else:
        #             if isinstance(value, _GenericAlias):
        #                 value = get_args(value)[0]
        #                 if value is str:
        #                     usage[f"<{key}>"] = "Text that needs to be put in quotes if it contains spaces."
        #                 elif value is int:
        #                     usage[f"<{key}>"] = "A number"
        #                 else:
        #                     usage[f"<{key}>"] = value.usage_description if hasattr(value, 'usage_description') else getdoc(value).splitlines()[0]
        #             usage[f"<{key}>"] = value.usage_description if hasattr(value, 'usage_description') else getdoc(value).splitlines()[0]
        if not self.docstring:
            return ""
        arg_match = self.args_regex.search(self.docstring)
        if arg_match:
            arg_lines = list(map(lambda x: x.strip(), arg_match.group('args').splitlines()))
            arg_lines = [arg_line for arg_line in arg_lines if arg_line != '']
            for line in arg_lines:
                try:
                    key, value = line.split(':', maxsplit=1)
                except ValueError as error:
                    log.debug(ic.format(self.name))
                    log.debug(ic.format(line))
                    log.debug(ic.format(arg_lines))
                    raise error
                if '(' in key:
                    key = key.split('(')[0]

                usage[f"<{key.strip()}>"] = value.strip()

        usage_line = "@AntiPetros "
        if self.parent is not None:
            usage_line += f"<{self.parent.name} or parent alias> "
        usage_line += f"<{self.name} or alias> "
        usage_explanation = []
        for key, value in usage.items():
            usage_line += f"{key} "
            value = '\n'.join(map(lambda x: x.strip(), re.split(r"\,|\.", value)))
            usage_explanation.append(f"{key}\n{value.strip()}\n-----")
        full_usage = usage_line.strip() + '\n' + '▬' * len(usage_line) + '\n' + '\n'.join(usage_explanation)
        return full_usage

    @usage.setter
    def usage(self, value):
        self._old_data['usage'] = value

    @property
    def signature(self):
        signature = inspect.signature(self.callback).parameters
        signature = {key: value for key, value in signature.items() if key not in ['self', 'ctx']}

        return signature

    @signature.setter
    def signature(self, value):
        self._old_data["signature"] = value

    @property
    def example(self):
        example = self.data_getters['meta_data']('example', 'NA')

        if self.cog.bot.bot_member is not None:
            return example.replace(self.bot_mention_placeholder, self.cog.bot.bot_member.mention)
        else:
            return example

    @example.setter
    def example(self, value):
        self.data_setters['meta_data']('example', value)

    @property
    def gif(self):
        gif_path = self.data_getters['meta_data']('gif', None)
        return gif_path

    @property
    def github_link(self):
        return self.data_getters['source_code']('link')

    @property
    def github_wiki_link(self):
        return self.data_getters['source_code']('wiki_link')

    @property
    def allowed_channels(self):
        if self.parent is not None:
            return self.parent.allowed_channels
        allowed_channels = []
        for check in self.checks:
            if hasattr(check, "allowed_channels"):
                allowed_channels += check.allowed_channels(self)
        if allowed_channels == []:
            return []
        if len(allowed_channels) > 1 and 'all' in allowed_channels:
            allowed_channels.remove('all')
        return list(map(self.bot.channel_from_name, allowed_channels))

    @property
    def allowed_roles(self):
        if self.parent is not None:
            return self.parent.allowed_roles
        allowed_roles = []
        for check in self.checks:
            if hasattr(check, "allowed_roles"):
                allowed_roles += check.allowed_roles(self)
        if allowed_roles == []:
            return []
        if len(allowed_roles) > 1 and 'all' in allowed_roles:
            allowed_roles.remove('all')
        return list(map(self.bot.role_from_string, allowed_roles))

    @property
    def allowed_in_dms(self):
        values = []
        for check in self.checks:
            if hasattr(check, "allowed_in_dm"):
                values.append(check.allowed_in_dm(self))
        if values == []:
            return True
        return all(values)

    @property
    def allowed_members(self):
        if self.parent is not None:
            return self.parent.allowed_members
        allowed_members = []
        for check in self.checks:
            if hasattr(check, "allowed_members"):
                allowed_members += check.allowed_members(self)
        if allowed_members == []:
            return set([self.bot.member_by_name('all')])
        if len(allowed_members) > 1 and 'all' in allowed_members:
            allowed_members.remove('all')
        if allowed_members == ['all']:
            return set([self.bot.member_by_name('all')])
        return set(allowed_members)

    def dump(self):
        return self.schema.dump(self)

    def __hash__(self) -> int:
        return hash((self.name, self.cog_name, self.docstring))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.__hash__() == o.__hash__()
        return False

    def __repr__(self):
        return f"{super().__class__.__name__}({self.__class__.__name__})"

    def __str__(self):
        if self.parent is not None:
            return f"{self.parent.name} {self.name}"
        return self.name


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
