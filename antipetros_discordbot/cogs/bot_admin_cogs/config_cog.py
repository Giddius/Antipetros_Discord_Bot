

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from configparser import ConfigParser, NoOptionError, NoSectionError
from collections import namedtuple
from typing import List
from datetime import datetime, timedelta, timezone
from textwrap import dedent
from pprint import pformat
from io import BytesIO
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from fuzzywuzzy import process as fuzzprocess
from discord.ext import commands
from typing import TYPE_CHECKING
from asyncstdlib.builtins import map as amap
from functools import partial, partialmethod
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import make_config_name, make_other_source_code_images, delete_message_if_text_channel, make_other_source_code_images_to_pil
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, log_invoker, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writejson, bytes2human
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker

from antipetros_discordbot.auxiliary_classes.for_cogs.aux_config_cog import AddedAliasChangeEvent
from antipetros_discordbot.utility.converters import CommandConverter
from antipetros_discordbot.utility.exceptions import ParameterErrorWithPossibleParameter

from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory
from antipetros_discordbot.utility.general_decorator import async_log_profiler, sync_log_profiler, universal_log_profiler

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


# endregion[Constants]

# region [Helper]


# endregion [Helper]


class ConfigCog(AntiPetrosBaseCog, command_attrs={'hidden': True, 'categories': CommandCategory.META}):
    """
    Cog with commands to access and manipulate config files, also for changing command aliases.
    Almost all are only available in DM's

    commands are hidden from the help command.
    """
    # region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.OPEN_TODOS | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.NEEDS_REFRACTORING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {"notify_when_changed": "yes",
                                            "notify_via": "bot-testing",
                                            "notify_roles": 'call'}}
    config_dir = APPDATA['config']
    alias_file = pathmaker(APPDATA['fixed_data'], "documentation", "command_aliases.json")

    required_folder = [RequiredFolder(config_dir)]
    required_files = [RequiredFile(alias_file, {}, RequiredFile.FileType.JSON)]
    status_bool_string_map = {"1": "ENABLED",
                              "0": "DISABLED"}
# endregion[ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.all_configs = [BASE_CONFIG, COGS_CONFIG]
        self.aliases = {}
        self.ready = False
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]


    @universal_log_profiler
    async def on_ready_setup(self):
        """
        standard setup async method.
        The Bot calls this method on all cogs when he has succesfully connected.
        """

        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Properties]

    @property
    @universal_log_profiler
    def existing_configs(self):
        existing_configs = {}
        for file in os.scandir(self.config_dir):
            if file.is_file() and file.name.endswith('.ini'):
                existing_configs[file.name.casefold().split('.')[0]] = pathmaker(file.path)
        return existing_configs

    @property
    @universal_log_profiler
    def notify_when_changed(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_when_changed', typus=bool, direct_fallback=False)

    @property
    @universal_log_profiler
    def notify_via(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_via', typus=str, direct_fallback='bot-testing')

    @property
    @universal_log_profiler
    def notify_role_names(self):
        return COGS_CONFIG.retrieve(self.config_name, 'notify_roles', typus=List[str], direct_fallback=['admin'])

    @property
    @universal_log_profiler
    def all_alias_names(self):
        _out = []
        for key, value in self.aliases.items():
            _out.append(key)
            _out += value
        return _out
# endregion[Properties]

# region [HelperMethods]

    @universal_log_profiler
    async def get_notify_roles(self):
        return [await self.bot.role_from_string(role_name) for role_name in self.notify_role_names]

    @universal_log_profiler
    async def send_config_file(self, ctx, config_name):
        config_path = self.existing_configs.get(config_name)
        modified = datetime.fromtimestamp(os.stat(config_path).st_mtime).astimezone(timezone.utc)
        image = await make_other_source_code_images(readit(config_path), 'ini', 'dracula')

        embed_data = await self.bot.make_generic_embed(title=config_name.upper(),
                                                       footer={'text': "last modified:"},
                                                       timestamp=modified,
                                                       author='bot_author',
                                                       thumbnail='config',
                                                       image=image)
        await ctx.send(**embed_data)
        await ctx.send(file=discord.File(config_path))


# endregion [HelperMethods]

# region [Commands]

    @auto_meta_info_command(enabled=True)
    @ owner_or_admin()
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

    @ auto_meta_info_command()
    @ owner_or_admin()
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

    @auto_meta_info_command()
    @ owner_or_admin()
    @ log_invoker(log, 'critical')
    async def overwrite_config_from_file(self, ctx):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @ auto_meta_info_command()
    @ owner_or_admin()
    async def change_setting_to(self, ctx, config, section, option, value):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @ auto_meta_info_command()
    @ owner_or_admin()
    async def show_config_content(self, ctx: commands.Context, config_name: str = "all"):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @ auto_meta_info_command()
    @ owner_or_admin()
    async def show_config_content_raw(self, ctx: commands.Context, config_name: str = "all"):
        """
        NOT IMPLEMENTED
        """
        await self.bot.not_implemented(ctx)

    @ auto_meta_info_command()
    @ owner_or_admin()
    @ log_invoker(log, 'critical')
    async def add_alias(self, ctx: commands.Context, command: CommandConverter, new_alias: str):
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
        new_alias = new_alias.casefold()
        if new_alias in self.all_alias_names:
            await ctx.send(f'Alias `{new_alias}` is already in use, either on this command or any other. Cannot be set as alias, aborting!')
            return
        add_success = await command.set_alias(new_alias)
        if add_success is True:
            await ctx.send(f"successfully added `{new_alias}` to the command aliases of `{command.name}`")
            await self.bot.creator.member_object.send(f"A new alias was set by `{ctx.author.name}`\n**Command:** `{command.name}`\n**New Alias:** `{new_alias}`")
        else:
            await ctx.send(f"error with adding alias `{new_alias}` to `{command.name}`, alias was **NOT** added!")

    @ auto_meta_info_command(aliases=["profiling"])
    @ owner_or_admin()
    @ log_invoker(log, 'critical')
    async def profiling_switch(self, ctx: commands.Context, action: str = "status"):
        action_map = {'status': self._report_profiling_enabled,
                      'enable': partial(self._changed_profiling_enabled, new_status="1"),
                      'disable': partial(self._changed_profiling_enabled, new_status="0"),
                      'switch': self._changed_profiling_enabled}
        if action.casefold() not in action_map:
            raise ParameterErrorWithPossibleParameter('action', action, list(action_map.keys()))
        await action_map.get(action)(ctx)
# endregion [Commands]

# region [Helper]

    @universal_log_profiler
    async def _report_profiling_enabled(self, ctx: commands.Context):
        status = os.getenv('ANTIPETROS_PROFILING')
        status = self.status_bool_string_map.get(status)
        await ctx.send(f"Profiling is currently {status}", delete_after=120)
        await delete_message_if_text_channel(ctx)

    @universal_log_profiler
    async def _changed_profiling_enabled(self, ctx: commands.Context, new_status: str = None):

        current_status = os.getenv('ANTIPETROS_PROFILING')

        if new_status == current_status:
            status_string = self.status_bool_string_map(current_status)
            await ctx.send(f"Profiling is already {status_string}!", delete_after=120)
            await delete_message_if_text_channel(ctx)
            return

        if new_status is None:
            change_to = "1" if current_status == "0" else "0"
            BASE_CONFIG.set('profiling', "enable_profiling", change_to)
            await ctx.send(f"Profiling has been {self.status_bool_string_map.get(change_to)}", delete_after=120)
            await delete_message_if_text_channel(ctx)
            return

        BASE_CONFIG.set('profiling', "enable_profiling", new_status)
        await ctx.send(f"Profiling has been {self.status_bool_string_map.get(new_status)}", delete_after=120)
        await delete_message_if_text_channel(ctx)
        return

    @universal_log_profiler
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
    bot.add_cog(ConfigCog(bot))
