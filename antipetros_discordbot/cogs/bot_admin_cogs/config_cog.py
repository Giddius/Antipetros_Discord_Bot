from __future__ import annotations

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from configparser import ConfigParser, NoOptionError, NoSectionError
from collections import namedtuple
from typing import List
from datetime import datetime, timedelta
from textwrap import dedent
from pprint import pformat
from io import BytesIO
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands
from typing import TYPE_CHECKING
from asyncstdlib.builtins import map as amap

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import make_config_name
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writejson, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_config_cog import AddedAliasChangeEvent
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "ConfigCog"
CONFIG_NAME = make_config_name(COG_NAME)

# endregion[Constants]

# region [Helper]

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Helper]


class ConfigCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Cog with commands to access and manipulate config files, also for changing command aliases.
    Almost all are only available in DM's

    commands are hidden from the help command.
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME
    config_dir = APPDATA['config']
    alias_file = APPDATA['command_aliases.json']
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.OPEN_TODOS | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING,
                             "2021-02-06 05:24:31",
                             "87f320af11ad9e4bd1743d9809c3af554bedab8efe405cd81309088960efddba539c3a892101943902733d783835373760c8aabbcc2409db9403366373891baf")}
    required_config_data = dedent("""
                                  notify_when_changed = yes
                                  notify_via = bot-testing
                                  notify_roles = call
                                """)
    # endregion[ClassAttributes]

    # region [Init]

    def __init__(self, bot: AntiPetrosBot):
        self.bot = bot
        self.support = self.bot.support
        self.all_configs = [BASE_CONFIG, COGS_CONFIG]
        self.aliases = {}
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):
        """
        standard setup async method.
        The Bot calls this method on all cogs when he has succesfully connected.
        """

        await self.refresh_command_aliases()
        await self.save_command_aliases()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Properties]

    @property
    def existing_configs(self):
        existing_configs = {}
        for file in os.scandir(self.config_dir):
            if file.is_file() and file.name.endswith('.ini'):
                existing_configs[file.name.casefold().split('.')[0]] = pathmaker(file.path)
        return existing_configs

    @property
    def notify_when_changed(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_when_changed', typus=bool, direct_fallback=False)

    @property
    def notify_via(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_via', typus=str, direct_fallback='bot-testing')

    @property
    def notify_role_names(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_roles', typus=List[str], direct_fallback=['admin'])

    @property
    def all_alias_names(self):
        _out = []
        for key, value in self.aliases.items():
            _out.append(key)
            _out += value
        return _out
# endregion[Properties]

# region [HelperMethods]

    async def get_notify_roles(self):
        return [await self.bot.role_from_string(role_name) for role_name in self.notify_role_names]

    async def save_command_aliases(self):
        writejson(self.aliases, self.alias_file)

    async def refresh_command_aliases(self):
        self.aliases = {}
        for cog_name, cog in self.bot.cogs.items():
            for command in cog.get_commands():
                self.aliases[command.name] = command.aliases
            await asyncio.sleep(0)

    async def send_config_file(self, ctx, config_name):
        config_path = self.existing_configs.get(config_name)
        modified = datetime.fromtimestamp(os.stat(config_path).st_mtime)
        size = bytes2human(os.stat(config_path).st_size, True)
        embed_data = await self.bot.make_generic_embed(title=config_name.upper(),
                                                       fields=[self.bot.field_item(name="__Size:__", value=size)],
                                                       footer={'text': "last modified:"},
                                                       timestamp=modified,
                                                       author='bot_author',
                                                       thumbnail='config')
        await ctx.send(**embed_data)
        await ctx.send(file=discord.File(config_path))


# endregion [HelperMethods]

# region [Commands]

    @auto_meta_info_command(enabled=True)
    @commands.is_owner()
    @log_invoker(log, 'info')
    async def list_configs(self, ctx):
        """
        Provides a list of all existing configs-files.

        The names are without the extension, and show up like they are needed as input for other config commands.

        """
        embed_data = await self.bot.make_generic_embed(title=f'Configs for {self.bot.display_name}',
                                                       description='```diff\n' + '\n'.join(self.existing_configs.keys()) + '\n```',
                                                       author='bot_author',
                                                       thumbnail='config')
        await ctx.reply(**embed_data)

    @ commands.command(aliases=get_aliases("config_request"))
    @ commands.is_owner()
    async def config_request(self, ctx, config_name: str = 'all'):
        """
        Returns a Config file as and attachment, with additional info in an embed.

        Args:
            config_name (str, optional): Name of the config, or 'all' for all configs. Defaults to 'all'.
        """
        if '.' in config_name:
            config_name = config_name.split('.')[0]
        mod_config_name = config_name.casefold()
        if mod_config_name not in list(self.existing_configs) + ['all']:
            await ctx.send(f'No Config named `{config_name}`, aborting!')
            return

        if config_name == 'all':
            for name in self.existing_configs:
                await self.send_config_file(ctx, name)
                await asyncio.sleep(0.5)
        else:
            await self.send_config_file(ctx, config_name)

    @ commands.command(aliases=get_aliases("overwrite_config_from_file"))
    @commands.is_owner()
    @log_invoker(log, 'critical')
    async def overwrite_config_from_file(self, ctx):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @commands.command(aliases=get_aliases("change_setting_to"))
    @commands.is_owner()
    async def change_setting_to(self, ctx, config, section, option, value):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @commands.command(aliases=get_aliases("show_config_content"))
    @commands.is_owner()
    async def show_config_content(self, ctx: commands.Context, config_name: str = "all"):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @commands.command(aliases=get_aliases("show_config_content_raw"))
    @commands.is_owner()
    async def show_config_content_raw(self, ctx: commands.Context, config_name: str = "all"):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @auto_meta_info_command(enabled=get_command_enabled("add_alias"))
    @owner_or_admin()
    @log_invoker(log, 'critical')
    async def add_alias(self, ctx: commands.Context, command_name: str, alias: str):
        """
        Adds an alias for a command.

        Alias has to be unique and not spaces.

        Args:
            command_name (str): name of the command
            alias (str): the new alias.

        Example:
            @AntiPetros add_alias flip_coin flip_it
        """
        await self.refresh_command_aliases()
        if command_name not in self.aliases:
            await ctx.send(f"I was not able to find the command with the name '{command_name}'")
            return
        if alias in self.all_alias_names:
            await ctx.send(f'Alias {alias} is already in use, either on this command or any other. Cannot be set as alias, aborting!')
            return
        self.aliases[command_name].append(alias)
        await self.save_command_aliases()
        await ctx.send(f"successfully added '{alias}' to the command aliases of '{command_name}'")
        await self.bot.reload_cog_from_command_name(command_name)
        await self.bot.creator.member_object.send(f"A new alias was set by `{ctx.author.name}`\n**Command:** {command_name}\n**New Alias:** {alias}")

# endregion [Commands]

# region [Helper]

    async def notify(self, event):
        roles = await self.get_notify_roles()
        embed_data = await event.as_embed_message()
        if self.notify_via.casefold() == 'dm':
            member_to_notify = list({role.members for role in roles})
            for member in member_to_notify:
                await member.send(**embed_data)

        else:
            channel = await self.bot.channel_from_name(self.notify_via)
            await channel.send(content=' '.join(role.mention for role in roles), **embed_data)


# endregion[Helper]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(ConfigCog(bot)))
