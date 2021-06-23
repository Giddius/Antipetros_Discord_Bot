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
from typing import Any
from inspect import getdoc
from functools import singledispatchmethod
import inspect
from inspect import Parameter
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
# * Local Imports ----------------------------------------------------------------------------------------------------------------------------------------------->

from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.engine.replacements.helper import JsonMetaDataProvider, JsonAliasProvider, SourceCodeProvider
from antipetros_discordbot.utility.checks import dynamic_enabled_checker
from antipetros_discordbot.schemas import AntiPetrosBaseCommandSchema
from antipetros_discordbot.engine.replacements.command_replacements.command_category import CommandCategory
from antipetros_discordbot.utility.gidtools_functions import pathmaker
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
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
        self.only_debug = kwargs.get('only_debug', False)
        self.clear_invocation = kwargs.get('clear_invocation', False)
        self.notifications = {self.experimental_notifier: kwargs.pop('experimental', False),
                              self.logged_notifier: kwargs.get('logged', False),
                              self.confirm_command_received_notifier: kwargs.get('confirm_command_received', False)}

    @property
    def bot(self):
        return self.cog.bot

    @property
    def confirm_command_received_emoji(self):
        return self.bot.salute_emoji

    def set_logged(self, value: bool):
        self.notifications[self.logged_notifier] = value

    async def experimental_notifier(self, ctx: commands.Context):
        text = f"**It could be broken or be changed/removed any time. Feel free to play around with it and please give Feedback to {self.bot.creator.mention} if you can!**"
        title = "WARNING THIS IS AN EXPERIMENTAL COMMAND"
        description = text
        thumbnail = "warning"
        embed_data = await self.bot.make_generic_embed(title=title, description=description, thumbnail=thumbnail)
        await ctx.temp_send(**embed_data, allowed_mentions=discord.AllowedMentions.none())
        channel_name = ctx.channel.name if ctx.channel.type is discord.ChannelType.text else 'DM'
        log.critical("command '%s' as '%s' -- invoked by: name: '%s', id: %s -- in channel: '%s' -- raw invoking message: '%s'",
                     ctx.command.name, ctx.invoked_with, ctx.author.name, ctx.author.id, channel_name, ctx.message.content)

    async def logged_notifier(self, ctx: commands.Context):
        title = "Logged"
        description = "The usage of this command was logged with your username"
        thumbnail = None
        footer = None
        embed_data = await self.bot.make_generic_embed(title=title, description=description, thumbnail=thumbnail, footer=footer)
        await ctx.temp_send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    async def confirm_command_received_notifier(self, ctx: commands.Context):
        await ctx.add_temp_reaction(self.confirm_command_received_emoji)

    async def call_before_hooks(self, ctx: commands.Context):
        await super().call_before_hooks(ctx)

        for notification_coro, enabled in self.notifications.items():
            if enabled:
                await notification_coro(ctx)

    async def call_after_hooks(self, ctx):
        await super().call_after_hooks(ctx)
        await ctx.delete_temp_items()
        if self.clear_invocation is True:
            asyncio.create_task(delete_message_if_text_channel(ctx))

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
        return self.data_setters['alias'](new_alias)

    async def get_source_code_image(self):
        return await asyncio.to_thread(self.data_getters['source_code'], typus='image')

    @property
    def enabled(self):
        if self.only_debug is True and self.bot.is_debug is False:
            return False
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
    def best_alias(self):
        return self.alias_data_provider.get_best_alias(self)

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
                    raise error
                if '(' in key:
                    key = key.split('(')[0]
                if key.casefold().strip() != 'args':
                    specifier = '[]' if "defaults" not in value.casefold() else '<>'
                    usage[f"{specifier[0]}{key.strip()}{specifier[1]}"] = value.strip()

        usage_line = "@AntiPetros "
        if self.parent is not None:
            usage_line += f"[{self.parent.name} | alias-of-{self.parent.name}] "
        usage_line += f"[{self.best_alias} | alias] "
        usage_explanation = []
        for key, value in usage.items():
            usage_line += f"{key} "
            value = '\n'.join(map(lambda x: x.strip(), re.split(r"\,|\.", value)))
            usage_explanation.append(f"{key}\n{value.strip()}\n-----")
        full_usage = usage_line.strip() + '\n' + '▬' * 10 + '\n' + '\n'.join(usage_explanation)
        return full_usage

    @usage.setter
    def usage(self, value):
        self._old_data['usage'] = value

    @property
    def signature(self):
        _out = {}
        signature = inspect.signature(self.callback).parameters
        for name, value in signature.items():
            if name not in ['self', 'ctx']:
                _out[name] = {'annotation': value.annotation if value.annotation is not Parameter.empty else '',
                              "default": value.default if value.default is not Parameter.empty else 'no-default',
                              "kind": str(value.kind)}

        return str(_out)

    @signature.setter
    def signature(self, value):
        self._old_data["signature"] = value

    @property
    def example(self):
        example = self.data_getters['meta_data']('example', 'NA')

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
                allowed_channels += list(check.allowed_channels(self))
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
                allowed_roles += list(check.allowed_roles(self))
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
                allowed_members += list(check.allowed_members(self))
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
