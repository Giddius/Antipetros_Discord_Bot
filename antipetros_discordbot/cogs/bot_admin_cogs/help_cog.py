# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import gc
import os
from enum import Enum

import asyncio
import unicodedata
from typing import Callable, List, Optional, TYPE_CHECKING, Union
from inspect import isclass
# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import aiohttp
import discord
from discord.ext import tasks, commands, flags
from async_property import async_property

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import delete_message_if_text_channel
from antipetros_discordbot.utility.checks import BaseAntiPetrosCheck
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus, ExtraHelpParameter, HelpCategory
from antipetros_discordbot.auxiliary_classes.help_dispatcher_mapping import HelpMethodDispatchMap
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink, make_box
from antipetros_discordbot.utility.converters import CategoryConverter, CogConverter, CommandConverter, HelpCategoryConverter, ExtraHelpParameterConverter
from antipetros_discordbot.utility.exceptions import ParameterError

from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand, CommandCategory, RequiredFile, RequiredFolder, auto_meta_info_command
from antipetros_discordbot.utility.general_decorator import is_refresh_task, universal_log_profiler
import inflect
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

if os.getenv('IS_DEV', 'false').casefold() == 'true':
    pass

# endregion[Imports]

# region [TODO]


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
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
inflect_engine = inflect.engine()

# endregion[Constants]

# region [Helper]


@universal_log_profiler
def no_filter(in_object):
    return True


@universal_log_profiler
def no_name_modifier(in_name: str) -> str:
    return in_name


@universal_log_profiler
def filter_with_user_role(owner_ids: List[int], in_member: discord.Member, only_working: bool = True, only_enabled: bool = True):
    role_names = ['all'] + [role.name.casefold() for role in in_member.roles]
    excluded_cogs = {'GeneralDebugCog', 'HelpCog'}

    def actual_filter(in_object):
        is_owner = False
        if in_member.id in owner_ids:
            is_owner = True
        if isinstance(in_object, (AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand)):
            if str(in_object.cog) in excluded_cogs:
                return False
            if only_enabled is True and in_object.enabled is False:
                return False
            if is_owner is True:
                return True
            if in_object.hidden is True and 'admin' not in role_names:
                return False
            allowed_roles = [c_role.casefold() for c_role in in_object.allowed_roles]
            return any(role in allowed_roles for role in role_names)
        elif isinstance(in_object, commands.Cog):

            if str(in_object) in excluded_cogs:
                return False
            if only_working is True and CogMetaStatus.WORKING not in in_object.meta_status:
                return False
            if is_owner is True:
                return True

            if in_object.public is False:
                return any(role in ['admin', 'admin lead'] for role in role_names)
            else:
                return True
        elif issubclass(in_object, CommandCategory):
            return in_object.visibility_check(in_member)
    return actual_filter

# endregion [Helper]


class HelpCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.META}):
    """
    WiP
    """
# region [ClassAttributes]

    public = True
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""

    base_config_section = 'help_settings'

    required_config_data = {'base_config': {base_config_section: {"general_description": "-file-",
                                                                  "restricted_to_dm": 'no',
                                                                  "delete_after_seconds": "0",
                                                                  "delete_invoking_message": "no"}},
                            'cogs_config': {}}

    data_folder = pathmaker(APPDATA['documentation'], 'help_data')
    general_help_description_file = pathmaker(data_folder, 'general_help_description.md')

    required_folder = [RequiredFolder(data_folder)]
    required_files = [RequiredFile(general_help_description_file, "WiP", RequiredFile.FileType.TEXT)]
    base_wiki_link = os.getenv('WIKI_BASE_URL')
    general_wiki_links = {'cog': '/'.join([base_wiki_link, 'cogs']),
                          'command': '/'.join([base_wiki_link, 'commands']),
                          'category': '/'.join([base_wiki_link, 'categories'])}
    max_comma_value = 900
    amount_preview_items = 10
# endregion [ClassAttributes]

# region [Init]

    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.help_dispatch_map = HelpMethodDispatchMap({AntiPetrosBaseCog: self._send_cog_help,
                                                        AntiPetrosBaseCommand: self._send_command_help,
                                                        AntiPetrosFlagCommand: self._send_command_help,
                                                        AntiPetrosBaseGroup: self._send_command_help,
                                                        CommandCategory: self._send_category_help,
                                                        HelpCategory.COG: self._general_cog_help,
                                                        HelpCategory.COMMAND: self._general_command_help,
                                                        HelpCategory.CATEGORY: self._general_category_help})

        self._current_cogs = None
        self._current_commands = None
        self._current_category_commands = None

        self.ready = False
        self.refresh_tasks = self.get_refresh_tasks()
        self.meta_data_setter('docstring', self.docstring)
        glog.class_init_notification(log, self)


# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def current_cogs(self):
        if self.ready is False:
            return None
        if self._current_cogs is None:

            self._current_cogs = dict(self.bot.cogs).copy()

        return self._current_cogs

    @property
    @universal_log_profiler
    def current_commands(self):
        if self.ready is False:
            return None
        if self._current_commands is None:
            self._current_commands = {command.name: command for command in self.bot.commands}
        return self._current_commands

    @property
    @universal_log_profiler
    def category_commands(self):
        if self.ready is False:
            return None
        if self._current_category_commands is None:
            self._current_category_commands = {}
            for command in self.bot.commands:
                for category_flag in command.categories.flags:
                    if category_flag not in self._current_category_commands:
                        self._current_category_commands[category_flag] = []
                    self._current_category_commands[category_flag].append(command)
        return self._current_category_commands

    @property
    @universal_log_profiler
    def general_help_description(self):
        if os.path.isfile(self.general_help_description_file) is False:
            writeit(self.general_help_description_file, 'WiP')
        from_config = BASE_CONFIG.retrieve(self.base_config_section, 'general_description', typus=str, direct_fallback='-file-')
        if from_config.casefold() == '-file-':
            return readit(self.general_help_description_file)
        return from_config

    @property
    @universal_log_profiler
    def restricted_to_dm(self):
        return BASE_CONFIG.retrieve(self.base_config_section, 'restricted_to_dm', typus=bool, direct_fallback=False)

    @property
    @universal_log_profiler
    def help_delete_after(self):
        seconds = BASE_CONFIG.retrieve(self.base_config_section, 'delete_after_seconds', typus=int, direct_fallback=0)
        if seconds == 0:
            return None
        return seconds

    @property
    @universal_log_profiler
    def delete_invoking_message(self):
        return BASE_CONFIG.retrieve(self.base_config_section, 'delete_invoking_message', typus=bool, direct_fallback=False)
# endregion [Properties]

# region [Setup]

    @universal_log_profiler
    async def on_ready_setup(self):
        self.update_current_cogs_and_commands_loop.start()
        self.ready = await asyncio.sleep(5, True)
        for refresh_task in self.refresh_tasks:
            asyncio.create_task(refresh_task())
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        if self.ready is False:
            return
        if any(_type in typus for _type in [UpdateTypus.CONFIG, UpdateTypus.COMMANDS, UpdateTypus.COGS]):
            for refresh_task in self.refresh_tasks:
                await refresh_task()
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=15, reconnect=True)
    async def update_current_cogs_and_commands_loop(self):
        if self.ready is False:
            return

        for refresh_task in self.refresh_tasks:

            asyncio.create_task(refresh_task())

# endregion [Loops]

# region [Listener]

# endregion [Listener]

# region [Commands]

    @auto_meta_info_command(categories=[CommandCategory.META])
    async def help(self, ctx: commands.Context, in_object: Optional[Union[HelpCategoryConverter, CommandConverter, CogConverter, CategoryConverter]], extra_parameter: Optional[ExtraHelpParameterConverter]):
        raw_params = ctx.message.content.split(ctx.invoked_with)[-1].strip()
        print(raw_params)
        author = await self.bot.retrieve_antistasi_member(ctx.author.id)
        if in_object is None and raw_params == '':
            async for embed_data in self.help_overview_embed(author, extra_parameter):
                await self._send_help(ctx, embed_data)

        elif in_object is None and raw_params != '':
            raise ParameterError('in_object', raw_params)
        else:
            await self.help_dispatch_map.get(in_object)(ctx, author, in_object, extra_parameter)

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


    @universal_log_profiler
    async def help_overview_embed(self, author: discord.Member, extra_parameter: ExtraHelpParameter = None):

        member_filter = filter_with_user_role(self.bot.owner_ids, author, True)
        data = {'cog': await self.get_cog_data(member_filter, self.remove_cog_suffix_cog_name_modifier),
                'command': await self.get_command_data(member_filter),
                'category': await self.get_category_data(member_filter)}
        fields = []
        for key, value in data.items():
            names = list(value)
            names = await self._sort_names(names, key)
            comma_value = await self._make_comma_value(names)
            wiki_link = embed_hyperlink(f'{inflect_engine.plural(key)} wiki page'.title(), self.general_wiki_links.get(key))
            fields.append(self.bot.field_item(name=f'**Possible *__`{key.title()}`__* values**',
                                              value=f"{ZERO_WIDTH}\n{wiki_link}\n{ZERO_WIDTH}\n> Use `help {inflect_engine.plural(key).lower()}` to get a detailed list of all possible {key.lower()} values.\n{ZERO_WIDTH}\n" +
                                              comma_value + f"\n{ZERO_WIDTH}",
                                              inline=False))
        # fields.append(self.bot.field_item(name='Possible Source-Code-Items values',
        #                                   value="Use `source-code-items` to get the list of possible source-code-item values",
        #                                   inline=False))
        links = f"{embed_hyperlink('GITHUB REPO', self.bot.github_url)}\n{embed_hyperlink('GIHUB WIKI',self.base_wiki_link)}"
        description = f"{make_box(links)}\n{ZERO_WIDTH}\n" + '\n'.join(f"> {line}" for line in self.general_help_description.splitlines()) + f"\n{ZERO_WIDTH}"
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title='GENERAL HELP',
                                                                            description=description,
                                                                            thumbnail="help",
                                                                            color="GIDDIS_FAVOURITE",
                                                                            timestamp=None,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

    @universal_log_profiler
    async def help_cogs_embed(self, author: discord.Member, extra_parameter: ExtraHelpParameter = None):
        member_filter = filter_with_user_role(self.bot.owner_ids, author, False)
        fields = []
        cog_data = await self.get_cog_data(cog_filter=member_filter)
        for cog_name, cog in cog_data.items():
            wiki_link = embed_hyperlink(f"{cog_name} {'wiki page'.title()}", cog.github_wiki_link)
            fields.append(self.bot.field_item(name=cog_name, value=f"{ZERO_WIDTH}\n{wiki_link}\n{ZERO_WIDTH}\n" + '\n'.join(f"> {line}"for line in cog.description.splitlines()) + f"\n{ZERO_WIDTH}", inline=False))

        # TODO: change links to link to the cogs folder and to the cogs wiki title page
        links = f"{embed_hyperlink('GITHUB REPO', self.bot.github_url)}\n{embed_hyperlink('COGS GITHUB WIKI',self.general_wiki_links.get('cog'))}"
        # TODO: create cogs thumbnail
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="Cogs Help",
                                                                            description=make_box(links) + f"\n{ZERO_WIDTH}",
                                                                            thumbnail="help",
                                                                            color="GIDDIS_FAVOURITE",
                                                                            timestamp=None,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

    @universal_log_profiler
    async def help_commands_embed(self, author: discord.Member, extra_parameter: ExtraHelpParameter = None):
        member_filter = filter_with_user_role(self.bot.owner_ids, author, True)
        fields = []
        command_data = await self.get_command_data(command_filter=member_filter)
        frequency_dict = await self.bot.get_command_frequency(from_datetime=None, to_datetime=None, as_counter=True)
        command_data = {key: value for key, value in sorted(command_data.items(), key=lambda x: (frequency_dict.get(x[0], 0), x[0]), reverse=True)}
        for command_name, command in command_data.items():
            wiki_link = embed_hyperlink(f"{command_name} {'wiki page'.title()}", command.github_wiki_link)
            fields.append(self.bot.field_item(name=command_name, value=f"{ZERO_WIDTH}\n{wiki_link}\n{ZERO_WIDTH}\n" + '\n'.join(f"> {line}"for line in command.brief.splitlines()) + f"\n{ZERO_WIDTH}", inline=False))

        # TODO: change links to link to the cogs folder and to the cogs wiki title page
        links = f"{embed_hyperlink('GITHUB REPO', self.bot.github_url)}\n{embed_hyperlink('COMMANDS GITHUB WIKI',self.general_wiki_links.get('command'))}"
        # TODO: create cogs thumbnail
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="Commands Help",
                                                                            description=make_box(links) + f"\n{ZERO_WIDTH}",
                                                                            thumbnail="help",
                                                                            color="GIDDIS_FAVOURITE",
                                                                            timestamp=None,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

    @universal_log_profiler
    async def help_categories_embed(self, author: discord.Member, extra_parameter: ExtraHelpParameter = None):
        member_filter = filter_with_user_role(self.bot.owner_ids, author, True)
        fields = []
        categories_data = await self.get_category_data(category_filter=member_filter)

        for category_name, category in categories_data.items():
            wiki_link = embed_hyperlink(f'{category_name} {"wiki page.title()"}', category.github_wiki_link)
            fields.append(self.bot.field_item(name=category_name, value=f"{ZERO_WIDTH}\n{wiki_link}\n{ZERO_WIDTH}\n" + '\n'.join(f" > {line}"for line in category.short_doc.splitlines()) + f"\n{ZERO_WIDTH}", inline=False))

        # TODO: change links to link to the cogs folder and to the cogs wiki title page
        links = f"{embed_hyperlink('GITHUB REPO', self.bot.github_url)}\n{embed_hyperlink('CATEGORIES GITHUB WIKI',self.general_wiki_links.get('category'))}"
        # TODO: create cogs thumbnail
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="Categories Help",
                                                                            description=make_box(links) + f"\n{ZERO_WIDTH}",
                                                                            thumbnail="help",
                                                                            color="GIDDIS_FAVOURITE",
                                                                            timestamp=None,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

    @universal_log_profiler
    async def help_specific_command_embed(self, author: discord.Member, command: Union[AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand], extra_parameter: ExtraHelpParameter = None):
        field_attr = ['signature', 'allowed_in_dms', 'enabled']

        fields = []
        for attr in field_attr:
            fields.append(self.bot.field_item(name=attr, value=getattr(command, attr)))

        fields.append(self.bot.field_item(name='aliases', value='\n'.join(f"`{item}`" for item in command.aliases) if command.aliases else "`None`"))

        fields.append(self.bot.field_item(name='allowed channels'.title(), value='\n'.join([f"`{item}`" for item in command.allowed_channels if await self._check_channel_visibility(author, item) is True])))
        fields.append(self.bot.field_item(name='allowed roles'.title(), value='\n'.join([f"`{item}`" for item in command.allowed_roles])))

        fields.append(self.bot.field_item(name='example', value=f"```css\n{command.example}\n```"))
        links = f"{embed_hyperlink(f'{command.name.upper()} GITHUB REPO', command.github_link)}\n{embed_hyperlink(f'{command.name.upper()} GITHUB WIKI',command.github_wiki_link)}"
        embed_data = await self.bot.make_generic_embed(title=command.name + ' HELP',
                                                       description=f"{links}\n{ZERO_WIDTH}\n" + '\n'.join(f"> {line}" for line in command.description.splitlines()),
                                                       thumbnail=await command.get_source_code_image(),
                                                       image=command.gif,
                                                       url=command.github_link,
                                                       fields=fields,
                                                       author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url})
        return embed_data
# endregion[Embeds]

# region [HelperMethods]

    @universal_log_profiler
    async def _check_channel_visibility(self, author: discord.Member, channel_name: str):
        channel = await self.bot.channel_from_name(channel_name)
        channel_member_permissions = channel.permissions_for(author)
        if channel_member_permissions.administrator is True or channel_member_permissions.read_messages is True:
            return True
        return False

    @ universal_log_profiler
    def get_refresh_tasks(self):
        _out = []
        from inspect import getmembers
        for meth_name, meth in getmembers(self):
            if hasattr(meth, 'is_refresh_task') and meth.is_refresh_task is True:
                _out.append(meth)
                log.debug('refresh task found: %s | %s', meth_name, str(meth))
        return _out

    @ universal_log_profiler
    async def _general_cog_help(self, ctx: commands.Context, in_object, extra_parameter: ExtraHelpParameter = None):
        async for embed_data in self.help_cogs_embed(ctx.author):
            await self._send_help(ctx, embed_data)

    @ universal_log_profiler
    async def _general_command_help(self, ctx: commands.Context, in_object, extra_parameter: ExtraHelpParameter = None):
        async for embed_data in self.help_commands_embed(ctx.author):
            await self._send_help(ctx, embed_data)

    @ universal_log_profiler
    async def _general_category_help(self, ctx: commands.Context, in_object, extra_parameter: ExtraHelpParameter = None):
        async for embed_data in self.help_categories_embed(ctx.author):
            await self._send_help(ctx, embed_data)

    @ universal_log_profiler
    async def _sort_names(self, names: list, key: str):
        if key == "command":
            frequency_dict = await self.bot.get_command_frequency(from_datetime=None, to_datetime=None, as_counter=True)
            return sorted(names, key=lambda x: (frequency_dict.get(x, 0), x), reverse=True)
        else:
            return names

    @ universal_log_profiler
    async def _make_comma_value(self, in_data: list):
        mod_in_data = in_data[:self.amount_preview_items]
        comma_value = ', '.join(f"`{item}`" for item in mod_in_data)
        original_length_in_data = len(in_data)
        lenght_comma_value = len(comma_value)
        while lenght_comma_value >= self.max_comma_value:
            _ = mod_in_data.pop(-1)
            comma_value = ', '.join(f"`{item}`" for item in in_data)
            lenght_comma_value = len(comma_value)
        if len(mod_in_data) != original_length_in_data:
            return comma_value + '...'
        return comma_value

    # @universal_log_profiler
    # async def _send_overall_help(self, ctx: commands.Context):
    #     member_filter = filter_with_user_role(self.bot.owner_ids, await self.bot.retrieve_antistasi_member(ctx.author.id), True)
    #     cogs = await self.all_cogs(member_filter, self.remove_cog_suffix_cog_name_modifier)
    #     log.debug('preparing help embed')
    #     fields = []
    #     for cog_name, cog in cogs.items():
    #         if cog_name.casefold() != "generaldebug":
    #             value_text = f"> *{cog.description}*\n{ZERO_WIDTH}\n"
    #             command_names = [f"`{command.name}`" if command.enabled is True else f"`{command.name}`" for command in cog.get_commands() if member_filter(command) is True]
    #             command_names.sort()
    #             # value_sub_text = f"{ListMarker.circle_star} **Commands:**\n"

    #             value_sub_text = '\n'.join(f"{SPECIAL_SPACE*0}{ListMarker.triangle} {command_name}" for command_name in command_names)
    #             value_sub_text += ''
    #             value_text += '\n'.join(map(lambda x: f"{SPECIAL_SPACE*16}{x}", make_box(value_sub_text).splitlines()))
    #             fields.append(self.bot.field_item(name=f"{ListMarker.bullet} {split_camel_case_string(cog_name).title()}", value=value_text))

    #     fields.append(self.bot.field_item(name=f"{ListMarker.bullet} Command Tool Sets", value=f'{ZERO_WIDTH}\n' + '\n'.join(f"{SPECIAL_SPACE*8}{ListMarker.circle_star} *{category}*" for category in await self.all_categories(member_filter))))
    #     async for embed_data in self.bot.make_paginatedfields_generic_embed(title='General Help', description=self.general_help_description,
    #                                                                         fields=fields,
    #                                                                         thumbnail='help',
    #                                                                         color="GIDDIS_FAVOURITE",
    #                                                                         timestamp=None):
    #         await ctx.send(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @ universal_log_profiler
    async def _send_cog_help(self, ctx: commands.Context, author: discord.Member, cog: commands.Cog, extra_parameter: ExtraHelpParameter = None):
        await ctx.send('cog')

    @ universal_log_profiler
    async def _send_command_help(self, ctx: commands.Context, author: discord.Member, command: Union[AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand], extra_parameter: ExtraHelpParameter = None):
        embed_data = await self.help_specific_command_embed(author, command, extra_parameter)
        await ctx.send(**embed_data)

    @ universal_log_profiler
    async def _send_category_help(self, ctx: commands.Context, category: CommandCategory, extra_parameter: ExtraHelpParameter = None):
        await ctx.send('toolbox')

    @ universal_log_profiler
    async def _send_check_help(self, ctx: commands.Context, check: BaseAntiPetrosCheck, extra_parameter: ExtraHelpParameter = None):
        await ctx.send('check')

    @ universal_log_profiler
    async def get_command_data(self, command_filter: Callable = no_filter, command_name_modifier: Callable = no_name_modifier):
        _out = {}
        for command_name, command in self.current_commands.items():
            if command_filter(command) is True:
                _out[command_name_modifier(command_name)] = command
        return _out

    @ universal_log_profiler
    async def get_cog_data(self, cog_filter: Callable = no_filter, cog_name_modifier: Callable = no_name_modifier):
        _out = {}
        if self._current_cogs is None:
            await self.refresh_current_cogs()
        for cog_name, cog in self.current_cogs.items():
            if cog_filter(cog) is True:
                _out[cog_name_modifier(cog_name)] = cog
        return _out

    @ universal_log_profiler
    async def get_category_data(self, category_filter: Callable = no_filter, category_name_modifier: Callable = no_name_modifier):
        _out = {}
        for category_name, category_member in CommandCategory.all_command_categories.items():
            if category_filter(category_member) is True:
                _out[category_name_modifier(str(category_member))] = category_member
        return _out

    @ staticmethod
    @ universal_log_profiler
    def not_hidden_working_cog_filter(cog: commands.Cog):
        if cog.docattrs.get('show_in_readme') is False:
            return False
        if CogMetaStatus.WORKING not in cog.docattrs.get('is_ready'):
            return False
        return True

    @ staticmethod
    @ universal_log_profiler
    def remove_cog_suffix_cog_name_modifier(cog_name: str):
        return cog_name.removesuffix('Cog')

    # @ universal_log_profiler
    # def _get_dispatcher(self, in_object):
    #     for key, value in self.help_dispatch_map.items():
    #         if isclass(in_object):
    #             if issubclass(in_object, key):
    #                 return value
    #         if isinstance(key, type) and isinstance(in_object, key):
    #             return value
    #         if in_object is key:
    #             return value
    #     raise ParameterError('in_object', in_object)

    @ universal_log_profiler
    async def _send_help(self, ctx: commands.Context, help_msg: Union[str, dict, discord.Embed]):
        target = ctx
        delete_after = self.help_delete_after
        if self.restricted_to_dm is True:
            target = ctx.author
            delete_after = None

        if isinstance(help_msg, str):
            await self.bot.split_to_messages(target, help_msg, delete_after=delete_after)
        elif isinstance(help_msg, dict):
            await target.send(**help_msg, delete_after=delete_after)
        elif isinstance(help_msg, discord.Embed):
            await target.send(embed=help_msg, delete_after=delete_after)
        if self.delete_invoking_message is True:
            await delete_message_if_text_channel(ctx)

    @ universal_log_profiler
    @ is_refresh_task
    async def refresh_current_cogs(self):
        log.debug("refreshing '_current_cogs' for 'HelpCog'")
        self._current_cogs = dict(self.bot.cogs).copy()

    @ universal_log_profiler
    @ is_refresh_task
    async def refresh_current_commands(self):
        log.debug("refreshing '_current_commands' for 'HelpCog'")
        self._current_commands = {command.name: command for command in self.bot.commands}

    @ universal_log_profiler
    @ is_refresh_task
    async def refresh_current_category_commands(self):
        log.debug("refreshing '_current_category_commands' for 'HelpCog'")
        self._current_category_commands = {}
        for command in self.bot.commands:
            for category_flag in command.categories.flags:
                if category_flag not in self._category_commands:
                    self._current_category_commands[category_flag] = []
                self._current_category_commands[category_flag].append(await asyncio.sleep(0, command))


# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx: commands.Context):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def cog_unload(self):
        self.update_current_cogs_and_commands_loop.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(HelpCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
