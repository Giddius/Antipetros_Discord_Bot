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
from abc import ABC, ABCMeta, abstractmethod
# * Local Imports -->
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.misc import delete_message_if_text_channel, split_camel_case_string
from antipetros_discordbot.utility.checks import BaseAntiPetrosCheck
from antipetros_discordbot.utility.gidtools_functions import pathmaker, readit, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH, SPECIAL_SPACE, SPECIAL_SPACE_2, Seperators, ListMarker
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus, ExtraHelpParameter, HelpCategory
from datetime import datetime, timedelta, timezone, tzinfo
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink, make_box
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.converters import CategoryConverter, CogConverter, CommandConverter, HelpCategoryConverter, ExtraHelpParameterConverter
from antipetros_discordbot.utility.exceptions import ParameterError

from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand, CommandCategory, RequiredFile, RequiredFolder, auto_meta_info_command, auto_meta_info_group
from antipetros_discordbot.utility.general_decorator import is_refresh_task, universal_log_profiler
import inflect
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.auxiliary_classes.all_item import AllItem
from antipetros_discordbot.engine.replacements.helper.help_embed_builder import HelpEmbedBuilder
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


class AbstractGeneralHelpProvider(ABC):

    def __init__(self, in_builder: "GeneralHelpEmbedBuilder"):
        self.in_builder = in_builder
        self.bot = in_builder.bot
        self.invoker = in_builder.invoker
        self.ctx = in_builder.ctx

    @abstractmethod
    async def __call__(self):
        ...

    @classmethod
    @property
    @abstractmethod
    def provides(cls):
        ...


class GeneralHelpFieldsProviderBasic(AbstractGeneralHelpProvider):
    field_item = EmbedFieldItem
    provides = 'fields'
    command_list_usage = '@AntiPetros help command-list'
    category_list_usage = '@AntiPetros help category-list'
    general_usage = CodeBlock("<prefix> help <command-list, category-list or the name/alias of an command/category>", 'Less')
    examples = CodeBlock(f"{command_list_usage}\n{category_list_usage}\n@Antipetros help flip\n@AntiPetros help roll_dice text\n@AntiPetros help server?", "Less")

    async def __call__(self):
        fields = self.in_builder.default_fields.copy()
        fields.append(self.field_item(name='Prefixes you can use to invoke a command'.title(), value=ListMarker.make_list(self.bot.all_prefixes, indent=1, formatting='**')))
        fields.append(self.field_item(name='Special Command __`command-list`__', value="Lists all possible __commands__, that you are allowed to invoke.\nSubcommands do not get listed, they are listed at the parent commands help embed."))
        fields.append(self.field_item(name='Special Command __`category-list`__', value="Lists all possible __categories__, that you are allowed to use"))
        fields.append(self.field_item(name='general help usage'.title(), value=self.general_usage))
        fields.append(self.field_item(name='Examples', value=self.examples))
        return fields


class GeneralHelpImageProviderBasic(AbstractGeneralHelpProvider):
    provides = 'image'

    async def __call__(self):
        return self.bot.portrait_url


class GeneralHelpDescriptionProvider(AbstractGeneralHelpProvider):
    provides = 'description'

    async def __call__(self):
        # text = self.bot.description
        text = f"{self.bot.description}\n" + f"{ZERO_WIDTH}\n" * 2
        text += '\n' + Seperators.make_line() + '\n'
        text += f"{self.in_builder.default_description}\n" + f"{ZERO_WIDTH}\n" * 2
        # text += self.in_builder.default_description
        return text


class GeneralHelpEmbedBuilder:
    field_item = EmbedFieldItem
    parts = ["title", "description", "color", "timestamp", "footer", "image", "thumbnail", "fields", 'url', 'author']
    default_color = "GIDDIS_FAVOURITE"
    default_timestamp = datetime.now(tz=timezone.utc)
    default_footer = None
    default_image = None
    default_thumbnail = None

    def __init__(self, bot: "AntiPetrosBot", ctx: commands.Context):
        self.ctx = ctx
        self.bot = bot
        self.invoker = self.bot.get_antistasi_member(ctx.author.id)

    def add_provider(self, provider):
        setattr(self, provider.provides + '_provider', provider)

    @property
    def default_title(self):
        return f"{self.bot.name} Help"

    @property
    def default_url(self):
        return self.bot.github_wiki_url

    @property
    def default_author(self):
        return {'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}

    @property
    def default_description(self):
        return self.ctx.command.cog.general_help_description

    @property
    def default_fields(self):
        return [self.field_item(name="Wiki Link", value=embed_hyperlink('link 🔗', self.bot.github_wiki_url), inline=True)]

    async def to_dict(self):
        embed_dict = {}
        for attr in self.parts:
            if hasattr(self, attr + '_provider') and getattr(self, attr + '_provider') is not None:
                attr_func = getattr(self, attr + '_provider')
                embed_dict[attr] = await attr_func()
            else:
                embed_dict[attr] = getattr(self, "default_" + attr)
        return embed_dict

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

    required_config_data = {'base_config': {"general_description": "-file-",
                                            "restricted_to_dm": 'no',
                                            "delete_after_seconds": "0",
                                            "delete_invoking_message": "no"},
                            'cogs_config': {}}

    data_folder = pathmaker(APPDATA['documentation'], 'help_data')
    general_help_description_file = pathmaker(data_folder, 'general_help_description.md')

    required_folder = [RequiredFolder(data_folder)]
    required_files = [RequiredFile(general_help_description_file, "WiP", RequiredFile.FileType.TEXT)]
    base_wiki_link = os.getenv('WIKI_BASE_URL')

    max_comma_value = 900
    amount_preview_items = 10
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)

        self.ready = False
        self.meta_data_setter('docstring', self.docstring)

        glog.class_init_notification(log, self)


# endregion [Init]

# region [Properties]


    @property
    def message_delete_after(self):
        delete_after = BASE_CONFIG.retrieve(self.config_name, 'delete_after_seconds', typus=int, direct_fallback=0)
        if delete_after == 0:
            delete_after = None
        return delete_after

    @property
    def message_restrict_to_dm(self):
        restrict_to_dm = BASE_CONFIG.retrieve(self.config_name, 'restricted_to_dm', typus=bool, direct_fallback=False)
        return restrict_to_dm

    @property
    def message_delete_invoking(self):
        delete_invoking = BASE_CONFIG.retrieve(self.config_name, 'delete_invoking_message', typus=bool, direct_fallback=False)
        return delete_invoking

    @property
    def command_list_description(self):
        return BASE_CONFIG.retrieve(self.config_name, 'command_list_description', typus=str, direct_fallback='NA')

    @property
    def category_list_description(self):
        return BASE_CONFIG.retrieve(self.config_name, 'category_list_description', typus=str, direct_fallback='NA')

    @property
    def general_help_description(self):
        return BASE_CONFIG.retrieve(self.config_name, 'general_help_description', typus=str, direct_fallback='NA')

# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

# endregion [Listener]

# region [Commands]

    @auto_meta_info_group(categories=[CommandCategory.META], case_insensitive=False, invoke_without_command=True)
    async def help(self, ctx: commands.Context, *, in_object: Union[CommandConverter, CategoryConverter] = None):
        if in_object is None:
            await self.general_help(ctx)

        elif isinstance(in_object, CommandCategory):
            await self.command_help(ctx, in_object)

        elif isinstance(in_object, AntiPetrosBaseCommand):
            await self.category_help(ctx, in_object)

        else:
            await ctx.send(f"{in_object} seems to not match anything")

    @help.command(name='command_list', aliases=['list', 'commands'])
    async def help_command_list(self, ctx: commands.Context, hidden: str = None):
        show_hidden = False
        if hidden is not None and hidden.casefold() == 'hidden':
            show_hidden = True
        async for embed_data in self.command_list_embed(ctx, show_hidden=show_hidden):
            await self.send_help(ctx, embed_data)

    @help.command(name='category_list', aliases=['categories'])
    async def help_category_list(self, ctx: commands.Context):
        async for embed_data in self.command_category_list_embed(ctx):
            await self.send_help(ctx, embed_data)

# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


    async def general_help(self, ctx: commands.Context):
        builder = GeneralHelpEmbedBuilder(self.bot, ctx)
        builder.add_provider(GeneralHelpFieldsProviderBasic(builder))
        builder.add_provider(GeneralHelpImageProviderBasic(builder))
        builder.add_provider(GeneralHelpDescriptionProvider(builder))
        embed_dict = await builder.to_dict()
        async for embed_data in self.bot.make_paginatedfields_generic_embed(**embed_dict):
            await self.send_help(ctx, embed_data)

    async def command_category_list_embed(self, ctx: commands.Context):
        member = self.bot.get_antistasi_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author
        frequ_dict = await self.bot.get_command_frequency()
        member_roles = set([AllItem()] + [role for role in member.roles])
        if member.id in self.bot.owner_ids:
            categories = [category for _, category in CommandCategory.all_command_categories.items()]
        else:
            categories = [category for _, category in CommandCategory.all_command_categories.items() if any(member_role in category.allowed_roles for member_role in member_roles)]

        description = self.category_list_description
        thumbnail = "help"
        color = 'GIDDIS_FAVOURITE'
        github_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/blob/development/antipetros_discordbot/engine/replacements/command_replacements/command_category.py"
        github_wiki_url = self.base_wiki_link + '/categories'
        fields = [self.bot.field_item(name='Github Link', value=embed_hyperlink('link 🔗', github_url), inline=True),
                  self.bot.field_item(name='Wiki Link', value=embed_hyperlink('link 🔗', github_wiki_url), inline=True)]
        for category in categories:
            if category.commands:
                value = ListMarker.make_list([f"`{command}`" for command in sorted(category.commands, key=lambda x: frequ_dict.get(x.name, 0), reverse=True)])
                fields.append(self.bot.field_item(name=f"**{str(category).upper()}**" + f'\n{ZERO_WIDTH}\n*{category.description}*\n{ZERO_WIDTH}', value=value, inline=False))

        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="Category List", description=description,
                                                                            thumbnail=thumbnail,
                                                                            color=color,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

    async def command_list_embed(self, ctx: commands.Context, show_hidden: bool):
        member = self.bot.get_antistasi_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author

        frequ_dict = await self.bot.get_command_frequency()

        description = self.command_list_description
        thumbnail = "help"
        color = 'GIDDIS_FAVOURITE'
        github_url = "https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/development/antipetros_discordbot/cogs"
        github_wiki_url = self.base_wiki_link + '/commands'
        fields = [self.bot.field_item(name='Wiki Link', value=embed_hyperlink('link 🔗', github_wiki_url), inline=True)]
        cog_dict = await self._get_command_list(ctx)
        for cog, cog_commands in cog_dict.items():
            if cog.name.casefold() != 'generaldebugcog':
                if show_hidden is False:
                    cog_commands = [command for command in cog_commands if command.hidden is False]
                    if cog_commands:
                        value = ListMarker.make_list([f"`{command.best_alias}` -> {command.brief}" for command in sorted(cog_commands, key=lambda x: frequ_dict.get(x.name, 0), reverse=True) if await self.filter_single_command(member, command) is True])
                        fields.append(self.bot.field_item(name=f"**{split_camel_case_string(cog.name.removesuffix('Cog'))}**\n{ZERO_WIDTH}", value=value, inline=False))
        async for embed_data in self.bot.make_paginatedfields_generic_embed(title="Command List", description=description,
                                                                            thumbnail=thumbnail,
                                                                            color=color,
                                                                            fields=fields,
                                                                            author={'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}):
            yield embed_data

# endregion[Embeds]

# region [HelperMethods]

    async def _get_command_list(self, ctx: commands.Context):
        member = self.bot.get_antistasi_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author

        _out = {}
        for cog_name, cog in self.bot.cogs.items():
            _out[cog] = []
            for command in cog.all_commands:
                if await self.filter_single_command(member, command) is True:
                    _out[cog].append(command)
        return _out

    async def filter_single_command(self, member: discord.Member, command: commands.Command):
        if member.id in self.bot.owner_ids:
            return True
        member_roles = set([AllItem()] + [role for role in member.roles])
        allowed_roles = command.allowed_roles
        if not isinstance(allowed_roles, set):
            allowed_roles = set(allowed_roles)
        if any(member_role in allowed_roles for member_role in member_roles):
            return True
        return False

    async def filter_commands(self, member: discord.Member):
        member_roles = set([AllItem()] + [role for role in member.roles])
        all_commands = [command for command in self.bot.commands if 'general_debug_cog' not in command.module.casefold()]
        if member.id in self.bot.owner_ids:
            return all_commands
        _out = []
        for command in all_commands:
            if any(member_role in command.allowed_roles for member_role in member_roles):
                _out.append(command)

        return _out

    async def command_help(self, ctx: commands.Context, command: AntiPetrosBaseCommand):
        builder = HelpEmbedBuilder(self.bot, ctx.author, command)
        async for embed_data in builder.to_embed():
            await self.send_help(ctx, embed_data)

    async def category_help(self, ctx: commands.Context, command: AntiPetrosBaseCommand):
        builder = HelpEmbedBuilder(self.bot, ctx.author, command)
        async for embed_data in builder.to_embed():
            await self.send_help(ctx, embed_data)

    async def send_help(self, ctx: commands.Context, data: Union[dict, discord.Embed, str]):

        target = ctx if self.message_restrict_to_dm is False else ctx.author

        if isinstance(data, dict):
            await target.send(**data, delete_after=self.message_delete_after, allowed_mentions=discord.AllowedMentions.none())
        elif isinstance(data, discord.Embed):
            await target.send(embed=data, delete_after=self.message_delete_after, allowed_mentions=discord.AllowedMentions.none())
        else:
            await target.send(data, delete_after=self.message_delete_after, allowed_mentions=discord.AllowedMentions.none())

        if self.message_delete_after is True:
            await delete_message_if_text_channel(ctx)

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
