"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from io import BytesIO
from random import randint
from typing import List, Union
from inspect import getmembers
from datetime import datetime, timezone

# * Third Party Imports --------------------------------------------------------------------------------->
import arrow
import PIL.Image
import discord
from pytz import timezone
from discord import File
from discord import Color as DiscordColor
from discord import Embed
from discord.ext import commands, tasks
from dateparser import parse as date_parse
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.enums import EmbedType, UpdateTypus
from antipetros_discordbot.utility.exceptions import FuzzyMatchError
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.gidtools_functions import (loadjson, pathmaker, writejson, create_file, create_folder)
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
import re
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

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

# EmbedFieldItem = namedtuple("EmbedFieldItem", ['name', 'value', "inline"], defaults=(None, None, None))


class EmbedBuilder(SubSupportBase):
    """
    [summary]

    [extended_summary]

    Args:
        SubSupportBase ([type]): [description]

    Returns:
        [type]: [description]
    """
    embed_data_folder = pathmaker(APPDATA['fixed_data'], "embed_data")
    standard_embed_symbols_file = pathmaker(APPDATA["embed_data"], "embed_symbols.json")
    default_embed_data_file = pathmaker(APPDATA['default_embed_data.json'])
    error_embed_base_data_file = pathmaker(APPDATA['embed_data'], "error_embed_values.json")
    image_thumbnail_data_file = pathmaker(APPDATA['debug'], 'embe_image_thumbnail_data.json')
    embed_types_enum = EmbedType
    allowed_embed_types = [embed_type_member.value for embed_type_member in EmbedType]
    datetime_parser = date_parse
    datetime_int_parser = arrow.get
    generic_image_name_range = (1, 9999)
    field_item = EmbedFieldItem
    max_embed_size = 6000
    max_embed_fields = 20
    max_field_value_length = 1024
    value_split_regex = re.compile(r"[\n\s\.]")

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self._ensure_folder_exists()
        self.embed_build_recipes = None
        self.default_empty = Embed.Empty
        self.special_footers = {}
        self.special_authors = {}
        self.replacement_map = {}
        self.default_field_name_num = 1

        glog.class_init_notification(log, self)

    def _validate_color(self, color):
        if color is None:
            return self._validate_color(self.default_color)
        elif isinstance(color, str):
            if color == 'random':
                return self.bot.random_color.discord_color
            elif color == 'colorless':
                return self.bot.fake_colorless
            elif color.startswith('#'):
                h = color.lstrip('#')
                rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                return discord.Color.from_rgb(*rgb)
            else:
                try:
                    return self.bot.get_discord_color(color)
                except FuzzyMatchError:
                    return self.bot.get_discord_color(self.default_color)
        elif isinstance(color, DiscordColor):
            return color
        else:
            raise TypeError(f"'color' needs to either be a string or and discord_color not '{type(color)}'")

    def _validate_type(self, typus):
        if isinstance(typus, EmbedType):
            return typus.value
        elif isinstance(typus, str) and typus in self.allowed_embed_types:
            return typus
        else:
            raise KeyError(f"'type' either needs to be an 'EmbedType' enum or one of '{[embed_type_member.value for embed_type_member in EmbedType]}' not {typus}")

    def _validate_timestamp(self, timestamp):
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            return self.datetime_parser(timestamp)
        elif isinstance(timestamp, int):
            return self.datetime_int_parser(timestamp)
        elif timestamp is None:
            return Embed.Empty
        else:
            raise TypeError("'timestamp' has to be either of type 'datetime', 'str' or 'int' not '{type(timestamp)}'")

    def _validate_image(self, image):
        if isinstance(image, str):
            if os.path.isfile(image):
                file_name = os.path.basename(image).replace('_', '')

                file = File(fp=image, filename=file_name)
                image = f"attachment://{file_name}"
                return image, file
            if image in self.standard_embed_symbols:
                return self.standard_embed_symbols.get(image), None

            return image, None
        elif isinstance(image, PIL.Image.Image):
            log.debug('Image is a Pil image')
            with BytesIO() as image_binary:
                image_format = 'PNG' if image.format is None else image.format
                image.save(image_binary, image_format, optimize=True)
                image_binary.seek(0)
                file_name = f"image{randint(*self.generic_image_name_range)}.{image_format.lower()}"
                file = File(fp=image_binary, filename=file_name)
                image = f"attachment://{file_name}"
                return image, file
        elif isinstance(image, bytes):
            with BytesIO() as image_binary:
                image_binary.write(image)
                image_binary.seek(0)
                file_name = f"image{randint(*self.generic_image_name_range)}.png"
                file = File(fp=image_binary, filename=file_name)
                image = f"attachment://{file_name}"
                return image, file

        elif isinstance(image, discord.file.File):
            return f"attachment://{image.filename}", image

        elif image is None:
            return None, None
        else:
            raise TypeError(f"'image' has to be of type 'str' or '{type(PIL.Image.Image)}' and not '{type(image)}'")

    def _fix_field_item(self, field_item, ):
        if field_item.name in [None, '']:
            field_item = field_item._replace(name=str(self.default_field_name_num) + '.')
            self.default_field_name_num += 1
        if field_item.value in [None, '']:
            field_item = field_item._replace(value='None')
        if field_item.inline is None:
            field_item = field_item._replace(inline=self.default_inline_value)
        return field_item

    @staticmethod
    def _size_of_field(field):
        return len(field.name) + len(field.value)

    def split_value_for_length(self, in_data: str):
        if len(in_data) == 0:
            yield len(in_data)
        chunks = in_data.split('\n')
        new_data = ''
        while chunks != []:
            while chunks != [] and len(new_data) < self.max_field_value_length and len(new_data + '\n' + chunks[0]) < self.max_field_value_length:
                new_data += '\n' + chunks.pop(0)
            yield new_data
            new_data = ''
        if new_data:
            yield new_data

    def handle_paginated_field(self, embed, field_item, applied_fields):
        added = 0
        for value in self.split_value_for_length(field_item.value):
            new_field_item = self.field_item(name=field_item.name, value=value, inline=field_item.inline)
            field = self._fix_field_item(new_field_item)
            embed.add_field(name=field.name, value=field.value, inline=field.inline)
            added += 1

        return embed, applied_fields + added

    async def _paginatedfields_generic_embed_helper(self, fields, embed):

        applied_fields = 0
        embed, applied_fields = self.handle_paginated_field(embed, fields.pop(0), applied_fields)

        while len(fields) > 0 and (len(embed) + self._size_of_field(fields[0])) < self.max_embed_size and applied_fields < self.max_embed_fields:
            embed, applied_fields = self.handle_paginated_field(embed, fields.pop(0), applied_fields)

        return embed, fields

    async def make_paginatedfields_generic_embed(self, fields: List[EmbedFieldItem], **kwargs):
        is_first = True
        while len(fields) > 0:
            if is_first is False:
                kwargs['title'] = 'CONTINUED'
                kwargs['description'] = ZERO_WIDTH
            _embed_data = await self.make_generic_embed(**kwargs)
            _actual_embed = _embed_data.get('embed')
            if len(_actual_embed) > self.max_embed_size:
                # TODO: make custom error
                raise RuntimeError('Base embed without fields is already larger than max size')
            embed, fields = await self._paginatedfields_generic_embed_helper(fields, _actual_embed)
            _embed_data['embed'] = embed
            yield _embed_data
            is_first = False

    async def make_generic_embed(self, author: Union[str, dict, discord.Member] = None, footer: Union[str, dict] = None, fields: List[EmbedFieldItem] = None, **kwargs):
        if isinstance(author, str):
            author = self.special_authors.get(author, self.default_author) if author != 'not_set' else None
        elif isinstance(author, discord.Member):
            author = {"name": author.display_name, "icon_url": author.avatar_url}
        if isinstance(footer, str):
            footer = self.special_footers.get(footer, self.default_footer) if footer != 'not_set' else None

        files = []
        title = kwargs.get('title', self.default_title)
        url = kwargs.get('url', discord.Embed.Empty)

        generic_embed = Embed(title=title,
                              description=str(kwargs.get('description', self.default_description)),
                              color=self._validate_color(kwargs.get('color', self.default_color)),
                              timestamp=self._validate_timestamp(kwargs.get('timestamp', self.default_timestamp)),
                              url=url)

        image, image_file = self._validate_image(kwargs.get('image', None))
        files.append(image_file)
        thumbnail, thumbnail_file = self._validate_image(kwargs.get('thumbnail', self.default_thumbnail)) if kwargs.get('thumbnail', self.default_thumbnail) != 'no_thumbnail' else (None, None)
        files.append(thumbnail_file)

        if author is not None:
            generic_embed.set_author(**author)

        if footer is not None:
            footer = footer.copy()
            footer['text'] = f"{ZERO_WIDTH}\n" + footer['text']
            generic_embed.set_footer(**footer)
        if thumbnail is not None:
            generic_embed.set_thumbnail(url=thumbnail)
        if image is not None:
            generic_embed.set_image(url=image)

        if fields is not None:
            for field in fields:
                field = self._fix_field_item(field)
                generic_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        self.default_field_name_num = 1
        # if self.bot.is_debug:
        #     await self.save_embed_as_json(embed=generic_embed, save_name=kwargs.get('save_name', None))
        if self.is_debug is True:
            log.debug("Embed with title '%s' has a len of '%s'", kwargs.get('title', 'None'), str(len(generic_embed)))
        _out = {"embed": generic_embed}
        files = [file_item for file_item in files if file_item is not None]
        if len(files) == 1:
            _out["file"] = files[0]
        elif len(files) > 1:
            _out['files'] = files
        await self.save_image_and_thumbnail(generic_embed)
        return _out

    async def save_image_and_thumbnail(self, embed):
        if self.bot.is_debug is False:
            return
        data = loadjson(self.image_thumbnail_data_file)
        image_url = embed.image.url if embed.image is not None else None
        thumbnail_url = embed.thumbnail.url if embed.thumbnail is not None else None

        if image_url is not None and str(image_url) != "Embed.Empty":
            data.append(str(image_url))
        if thumbnail_url is not None and str(thumbnail_url) != "Embed.Empty":
            data.append(str(thumbnail_url))
        data = list(set(data))
        writejson(data, self.image_thumbnail_data_file)

    async def save_embed_as_json(self, embed, save_name: str = None):
        save_name = embed.title if save_name is None else save_name
        file_name = save_name.replace(' ', '_').replace('?', '').replace('!', '').replace('/', '').replace('"', '').replace("'", "").replace('*', '').replace('~', '').replace(ZERO_WIDTH, '').replace('\n', '').strip() + '.json'
        file_path = pathmaker(APPDATA["saved_embeds"], file_name)
        writejson(embed.to_dict(), file_path)

    async def make_cancelled_embed(self, title: str, msg: str, extra: str = None):
        embed = Embed(title=title, description=msg, color=discord.Color.red())
        embed.set_thumbnail(url=self.standard_embed_symbols.get("cross_mark"))
        if extra is not None:
            embed.add_field(name='Extra Info', value=extra, inline=False)
        return embed

    async def make_confirmed_embed(self):
        pass

    async def make_error_embed(self, ctx: commands.Context, error):
        base_data = self.error_embed_base_data
        embed = Embed(title=f"Error with Command {ctx.command}",
                      description=error.msg,
                      color=base_data.get('color'),
                      timestamp=datetime.utcnow())

        embed.set_thumbnail(url=base_data.get('thumbnail_url'))
        embed.set_author(**self.special_authors.get('bot_author'))
        return embed

    def collect_embed_build_recipes(self):
        self.embed_build_recipes = {}
        # for method_name, method_object in getmembers(self.__class__, iscoroutinefunction):
        for method_name, method_object in getmembers(self.__class__):
            if method_name.startswith('_embed_recipe_'):
                self.embed_build_recipes[method_name.replace("_embed_recipe_", "")] = getattr(self, method_name)

    @ property
    def error_embed_base_data(self):
        if os.path.isfile(self.error_embed_base_data_file) is False:
            writejson({}, self.error_embed_base_data_file)
        return loadjson(self.error_embed_base_data_file)

    @ property
    def standard_embed_symbols(self):
        create_file(self.standard_embed_symbols_file)
        return loadjson(self.standard_embed_symbols_file)

    @ property
    def folder_exists(self):
        return os.path.isdir(self.embed_data_folder)

    def _ensure_folder_exists(self):
        create_folder(self.embed_data_folder)
        if os.path.isfile(self.image_thumbnail_data_file) is False:
            writejson([], self.image_thumbnail_data_file)

    @ property
    def default_inline_value(self):
        """
        "default_inline_value": [true or false]
        """
        return loadjson(self.default_embed_data_file).get('default_inline_value')

    @ property
    def default_title(self):
        """
        "default_title": ""
        replace template strings:   - $BOT_NAME$ for bot.display_name

        """

        _out = loadjson(self.default_embed_data_file).get('default_title')
        for replace_marker, replace_value in self.replacement_map.items():
            _out = _out.replace(replace_marker, replace_value)
        return _out

    @ property
    def default_description(self):
        """
        "default_description": ""
        replace template strings:   - $BOT_NAME$ for bot.display_name
        """
        _out = loadjson(self.default_embed_data_file).get('default_description')
        for replace_marker, replace_value in self.replacement_map.items():
            _out = _out.replace(replace_marker, replace_value)
        return _out

    @ property
    def default_author(self):
        """
        "default_author": {"name": "", "url": "", "icon_url": ""}
        """
        return loadjson(self.default_embed_data_file).get('default_author')

    @ property
    def default_footer(self):
        """

        "default_footer": {"text": "", "icon_url": ""},

        """
        return loadjson(self.default_embed_data_file).get('default_footer')

    @ property
    def default_thumbnail(self):
        """

        "default_thumbnail": ""

        """
        return loadjson(self.default_embed_data_file).get('default_thumbnail')

    @ property
    def default_color(self):
        """
        "default_color": ""
        """
        return discord.Color.dark_theme()

    @ property
    def default_timestamp(self):
        """
        optional!
        "default_timestamp": ""
        """
        return loadjson(self.default_embed_data_file).get('default_timestamp', datetime.now(tz=timezone("Europe/Berlin")))

    @ property
    def default_type(self):
        return 'rich'

    async def on_ready_setup(self):
        self.special_authors = {'bot_author': {'name': self.bot.display_name, 'url': self.bot.github_url, 'icon_url': self.bot.user.avatar_url},
                                'default_author': self.default_author,
                                'armahosts': {'name': 'Server Provided by ARMAHOSTS🔗', "url": self.bot.armahosts_url, 'icon_url': self.bot.armahosts_icon}}
        self.special_footers = {'feature_request_footer': {'text': "For feature suggestions and feature request, contact @Giddi".title(), "icon_url": self.bot.creator.avatar_url},
                                'default_footer': self.default_footer,
                                'armahosts': {'text': self.bot.armahosts_footer_text + '\n' + self.bot.armahosts_url}}
        self.replacement_map = {"$BOT_NAME$": self.bot.display_name}
        self.collect_embed_build_recipes()
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return EmbedBuilder
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
