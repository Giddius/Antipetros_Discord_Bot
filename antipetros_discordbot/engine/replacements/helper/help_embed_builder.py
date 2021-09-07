"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ------------------------------------------------------------------------------------------------------------------------------------>

import gc
import os
import unicodedata

from abc import ABC, abstractmethod
from typing import Callable, Dict, TYPE_CHECKING, Union
from datetime import datetime, timezone
from functools import partial
from collections import UserDict


# * Third Party Imports ----------------------------------------------------------------------------------------------------------------------------------------->

import discord


from jinja2 import BaseLoader, Environment

from natsort import natsorted

from discord.ext import commands, tasks, flags, ipc

import gidlogger as glog

from antipetros_discordbot.auxiliary_classes.all_item import AllItem
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.general_decorator import handler_method, handler_method_only_commands
from async_property import async_property
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import CodeBlock
from antipetros_discordbot.utility.discord_markdown_helper.discord_formating_helper import embed_hyperlink
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ListMarker, SPECIAL_SPACE, ZERO_WIDTH
import inflect
import inspect
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand
from antipetros_discordbot.engine.replacements.helper import CommandCategory
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


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
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
inflect_engine = inflect.engine()
# endregion[Constants]


class StringKeyDict(UserDict):
    def __init__(self, in_dict: dict = None) -> None:
        super().__init__(__dict={str(key): value for key, value in in_dict.items()} if in_dict is not None else in_dict)

    def __setitem__(self, key, item):
        super().__setitem__(key=str(key), item=item)

    def __getitem__(self, key):
        return super().__getitem__(key=str(key))

    def __delitem__(self, key):
        super().__delitem__(key=str(key))

    def __contains__(self, key):
        return super().__contains__(key=str(key))

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[str(key)] = value
        return d


class AbstractProvider(ABC):
    field_item = EmbedFieldItem

    def __init__(self, in_builder: "HelpCommandEmbedBuilder"):
        self.bot = in_builder.bot
        self.in_object = in_builder.in_object
        self.member = in_builder.member

    @abstractmethod
    async def __call__(self):
        ...

    @classmethod
    @property
    @abstractmethod
    def provides(cls):
        ...

    @property
    def typus(self):
        if isinstance(self.in_object, CommandCategory):
            return 'categories'
        if isinstance(self.in_object, (AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand)):
            return 'commands'

    @property
    def is_group(self):
        return isinstance(self.in_object, commands.Group)

    @property
    def is_sub_command(self):
        if hasattr(self.in_object, 'parent'):
            return self.in_object.parent is not None
        return False

    @property
    def member_can_invoke(self):
        member_roles = set([AllItem()] + [role for role in self.member.roles])
        if self.member.id in self.bot.owner_ids:
            return True
        if set(self.in_object.allowed_roles).isdisjoint(member_roles) is False:
            return True
        try:
            if self.member in self.in_object.allowed_members or AllItem() in self.in_object.allowed_members:
                return True
        except TypeError:
            pass
        return False


class AbstractFieldProvider(AbstractProvider):
    provides = 'fields'

    def __init__(self, in_builder: "HelpCommandEmbedBuilder"):
        super().__init__(in_builder)
        self.all_handler = None
        self.field_name_handler = self._no_underscore_and_to_title
        self._set_handler_attribute()

    def _set_handler_attribute(self):
        self.all_handler = {}
        for method_name, method_object in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method_object, 'is_handler') and method_object.is_handler is True:
                self.all_handler[method_object.handled_attr] = method_object

    @ classmethod
    @ property
    def bool_symbol_map(cls) -> Dict[bool, str]:
        return NotImplemented

    async def handle_name(self, name):
        try:
            return await self.field_name_handler(name)
        except Exception:
            return name

    async def _no_underscore_and_to_title(self, in_data):
        return in_data.replace('_', ' ').title()

    async def _no_handling(self, in_data):
        return in_data

    def add_handler(self, new_handler: Callable):
        if not inspect.iscoroutinefunction(new_handler):
            raise TypeError('new_handler needs to be a coroutine')
        if not hasattr(new_handler, 'is_handler'):
            new_handler = handler_method(new_handler)
            self.all_handler[new_handler.handled_attr] = partial(new_handler, new_handler.handled_attr)


class DefaultTitleProvider(AbstractProvider):
    provides = 'title'

    async def __call__(self):
        if self.is_sub_command:
            return f"{self.in_object.parent.name} {self.in_object.name}"

        return self.in_object.name


class DefaultDescriptionProvider(AbstractProvider):
    provides = 'description'

    async def get_commands(self):

        frequ_dict = await self.bot.get_command_frequency()
        sorted_commands = sorted(getattr(self.in_object, 'commands'), key=lambda x: frequ_dict.get(x.name, 0), reverse=True)
        value = ListMarker.make_list([f"`{command}`" for command in sorted_commands])
        return '\n'.join(map(lambda x: f"{SPECIAL_SPACE*8}{x}", value.splitlines()))

    async def __call__(self):
        description = self.in_object.description
        if self.typus == 'categories':
            description = description + f'{ZERO_WIDTH}\n{ZERO_WIDTH}\n**Commands:**\n' + await self.get_commands()
        if self.member_can_invoke is False:
            description = f"__** You do not have the necesary roles to actually invoke this command**__\n{ZERO_WIDTH}\n" + description
        return description


class DefaulThumbnailProvider(AbstractProvider):
    provides = "thumbnail"

    async def __call__(self):

        if hasattr(self.in_object, 'gif') and self.in_object.gif is not None:
            return self.in_object.gif


class DefaulImageProvider(AbstractProvider):
    provides = "image"

    async def __call__(self):
        return None


class DefaultAuthorProvider(AbstractProvider):
    provides = "author"

    async def __call__(self):
        return {'name': self.bot.display_name, "url": self.bot.github_url, "icon_url": self.bot.portrait_url}


class DefaultfooterProvider(AbstractProvider):
    provides = 'footer'

    async def __call__(self):
        return None


class DefaulURLProvider(AbstractProvider):
    provides = 'url'

    async def __call__(self):
        return self.in_object.github_wiki_link


class DefaultFieldsProvider(AbstractFieldProvider):
    bool_symbol_map = {True: '✅',
                       False: '❎'}

    async def __call__(self):
        fields = []
        for handler_attr, handler_func in self.all_handler.items():
            handler_attr = handler_attr.removesuffix('_ca').removesuffix('_co')
            if hasattr(self.in_object, handler_attr) and handler_func.applicable_to in ['all', self.typus]:
                new_item = await handler_func()
                if new_item is not None:
                    fields.append(new_item)
        return fields

    @ property
    def visible_channels(self):
        _out = []
        for channel in self.in_object.allowed_channels:
            if channel.name.casefold() == 'all':
                _out.append(channel)

            else:
                channel_member_permissions = channel.permissions_for(self.member)
                if channel_member_permissions.administrator is True or all(perms is True for perms in [channel_member_permissions.read_messages, channel_member_permissions.send_messages]):
                    _out.append(channel)

        return set(_out)

    @ handler_method
    async def _handle_usage(self):
        attr_name = "usage"
        name = await self.handle_name(attr_name)
        value = CodeBlock(getattr(self.in_object, attr_name), 'css')
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_aliases(self):
        attr_name = "aliases"
        name = await self.handle_name(attr_name)
        items = [f"`{alias}`" for alias in sorted(getattr(self.in_object, attr_name))]
        value = ListMarker.make_list(items)
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method_only_commands
    async def _handle_allowed_members(self):
        attr_name = "allowed_members"
        name = await self.handle_name(attr_name)
        value = getattr(self.in_object, attr_name)
        if not value:
            value = None
        else:
            value = '\n'.join(member.mention for member in value)
        return self.field_item(name=name, value=value, inline=False)

    @ handler_method
    async def _handle_allowed_channels(self):
        attr_name = "allowed_channels"
        name = await self.handle_name(attr_name)
        channels = sorted(getattr(self.in_object, attr_name), key=lambda x: x.position)
        value = ListMarker.make_column_list([channel.mention for channel in channels if channel in self.visible_channels], ListMarker.star, amount_columns=1)
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_allowed_roles(self):
        attr_name = "allowed_roles"
        name = await self.handle_name(attr_name)
        roles = sorted(getattr(self.in_object, attr_name), key=lambda x: x.position)
        value = '\n'.join(f"`{role.name}`" for role in roles)
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_allowed_in_dms(self):
        attr_name = "allowed_in_dms"
        name = await self.handle_name(attr_name)
        value = self.bool_symbol_map.get(getattr(self.in_object, attr_name))
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    # @ handler_method
    # async def _handle_github_link(self):
    #     attr_name = "github_link"
    #     name = await self.handle_name(attr_name)
    #     value = embed_hyperlink('link 🔗', getattr(self.in_object, attr_name))
    #     inline = True
    #     return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_github_wiki_link(self):
        attr_name = "github_wiki_link"
        name = await self.handle_name(attr_name)
        value = embed_hyperlink('link 🔗', getattr(self.in_object, attr_name))
        inline = True
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_extra_info(self):
        attr_name = "extra_info"
        name = await self.handle_name(attr_name)
        attr_value = getattr(self.in_object, attr_name)
        if attr_value is None:
            return None
        value = f"`{attr_value}`"
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method
    async def _handle_example(self):
        attr_name = "example"
        name = await self.handle_name(attr_name)
        value = CodeBlock(getattr(self.in_object, attr_name), 'css')
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @ handler_method_only_commands
    async def _handle_commands_co(self):
        attr_name = "commands"
        name = await self.handle_name('sub_commands')
        value = ListMarker.make_list([f"`{command}`" for command in getattr(self.in_object, attr_name)])
        inline = False
        return self.field_item(name=name, value=value, inline=inline)

    @handler_method_only_commands
    async def _handle_hidden(self):
        attr_name = "hidden"
        name = await self.handle_name(attr_name)
        value = self.bool_symbol_map.get(getattr(self.in_object, attr_name))
        inline = True
        return self.field_item(name=name, value=value, inline=inline)

    @handler_method_only_commands
    async def _handle_enabled(self):
        attr_name = "enabled"
        name = await self.handle_name(attr_name)
        value = self.bool_symbol_map.get(getattr(self.in_object, attr_name))
        inline = True
        return self.field_item(name=name, value=value, inline=inline)


class DefaultColorProvider(AbstractProvider):
    provides = 'color'

    async def __call__(self):
        if isinstance(self.in_object, commands.Command):
            return self.in_object.cog.color
        return 'GIDDIS_FAVOURITE'


class DefaultTimestampProvider(AbstractProvider):
    provides = 'timestamp'

    async def __call__(self):
        return datetime.now(tz=timezone.utc)


class HelpEmbedBuilder:
    field_item = EmbedFieldItem

    default_title_provider = DefaultTitleProvider
    default_description_provider = DefaultDescriptionProvider
    default_thumbnail_provider = DefaulThumbnailProvider
    default_image_provider = DefaulImageProvider
    default_author_provider = DefaultAuthorProvider
    default_footer_provider = DefaultfooterProvider
    default_fields_provider = DefaultFieldsProvider
    default_url_provider = DefaulURLProvider
    default_color_provider = DefaultColorProvider
    default_Timestamp_provider = DefaultTimestampProvider

    def __init__(self, bot: "AntiPetrosBot", invoking_person: Union[discord.Member, discord.User], in_object: Union["AntiPetrosBaseCommand", "AntiPetrosBaseGroup", "AntiPetrosFlagCommand", CommandCategory]):
        self.bot = bot
        self.in_object = in_object
        self.member = self.bot.get_antistasi_member(invoking_person.id) if isinstance(invoking_person, discord.User) else invoking_person

        self.title_provider = self.default_title_provider(self)
        self.description_provider = self.default_description_provider(self)
        self.thumbnail_provider = self.default_thumbnail_provider(self)
        self.image_provider = self.default_image_provider(self)
        self.author_provider = self.default_author_provider(self)
        self.footer_provider = self.default_footer_provider(self)
        self.fields_provider = self.default_fields_provider(self)
        self.url_provider = self.default_url_provider(self)
        self.color_provider = self.default_color_provider(self)
        self.timestamp_provider = self.default_Timestamp_provider(self)

    def set_provider(self, provider: AbstractProvider):
        setattr(self, provider.provides + '_provider', provider(self))

    async def to_embed(self):
        embed_data = await self.bot.make_generic_embed(title=await self.title_provider(),
                                                       description=await self.description_provider(),
                                                       thumbnail=await self.thumbnail_provider(),
                                                       image=await self.image_provider(),
                                                       author=await self.author_provider(),
                                                       fields=await self.fields_provider(),
                                                       url=await self.url_provider(),
                                                       color=await self.color_provider(),
                                                       timestamp=await self.timestamp_provider())

        yield embed_data


# region[Main_Exec]


if __name__ == '__main__':
    pass
# endregion[Main_Exec]
