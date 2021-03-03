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
from pytz import timezone
from discord import File
from discord import Color as DiscordColor
from discord import Embed
from dateparser import parse as date_parse

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.enums import EmbedType
from antipetros_discordbot.utility.exceptions import FuzzyMatchError
from antipetros_discordbot.utility.named_tuples import EmbedFieldItem
from antipetros_discordbot.utility.gidtools_functions import (loadjson, pathmaker, writejson, create_file, create_folder)
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH

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
    embed_types_enum = EmbedType
    allowed_embed_types = [embed_type_member.value for embed_type_member in EmbedType]
    datetime_parser = date_parse
    datetime_int_parser = arrow.get
    generic_image_name_range = (1, 9999)
    field_item = EmbedFieldItem
    max_embed_size = 6000
    max_embed_fields = 25

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
        if isinstance(color, str):
            if color == 'random':
                return self.bot.random_color.discord_color
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
            with BytesIO() as image_binary:
                image_format = 'PNG' if image.format is None else image.format
                image.save(image_binary, image_format, optimize=True)
                image_binary.seek(0)
                file_name = f"image{randint(*self.generic_image_name_range)}.{image_format.lower()}"
                file = File(fp=image_binary, filename=file_name)
                image = f"attachment://{file_name}"
                return image, file
        elif image is None:
            return None, None
        else:
            raise TypeError(f"'image' has to be of type 'str' or '{type(PIL.Image.Image)}' and not '{type(image)}'")

    def _fix_field_item(self, field_item, ):
        if field_item.name is None:
            field_item = field_item._replace(name=str(self.default_field_name_num) + '.')
            self.default_field_name_num += 1
        if field_item.value is None:
            field_item = field_item._replace(value=ZERO_WIDTH)
        if field_item.inline is None:
            field_item = field_item._replace(inline=self.default_inline_value)
        return field_item

    @staticmethod
    def _size_of_field(field):
        return len(field.name) + len(field.value)

    def _paginatedfields_generic_embed_helper(self, fields, embed):
        amount_fields = len(fields)
        applied_fields = 0

        for _ in range(amount_fields):
            if (len(embed) + self._size_of_field(fields[0])) < self.max_embed_size and applied_fields < self.max_embed_fields:
                field = self._fix_field_item(fields.pop(0))
                embed.add_field(name=field.name, value=field.value, inline=field.inline)
                applied_fields += 1
            else:
                return embed, fields
        return embed, fields

    async def make_paginatedfields_generic_embed(self, fields: List[EmbedFieldItem], **kwargs):
        is_first = True
        while len(fields) > 0:
            if is_first is False:
                kwargs['title'] = 'CONTINUED'
            _embed_data = await self.make_generic_embed(**kwargs)
            _actual_embed = _embed_data.get('embed')
            if len(_actual_embed) > self.max_embed_size:
                # TODO: make custom error
                raise RuntimeError('Base embed without fields is already larger than max size')
            embed, fields = self._paginatedfields_generic_embed_helper(fields, _actual_embed)
            _embed_data['embed'] = embed
            yield _embed_data
            is_first = False

    async def make_generic_embed(self, author: Union[str, dict] = None, footer: Union[str, dict] = None, fields: List[EmbedFieldItem] = None, **kwargs):
        if isinstance(author, str):
            author = self.special_authors.get(author, self.default_author) if author != 'not_set' else None
        if isinstance(footer, str):
            footer = self.special_footers.get(footer, self.default_footer) if footer != 'not_set' else None

        files = []
        generic_embed = Embed(title=str(kwargs.get("title", self.default_title)),
                              description=str(kwargs.get('description', self.default_description)),
                              color=self._validate_color(kwargs.get('color', self.default_color)),
                              timestamp=self._validate_timestamp(kwargs.get('timestamp', self.default_timestamp)),
                              type=self._validate_type(kwargs.get('type', self.default_type)))

        image, image_file = self._validate_image(kwargs.get('image', None))
        files.append(image_file)
        thumbnail, thumbnail_file = self._validate_image(kwargs.get('thumbnail', self.default_thumbnail)) if kwargs.get('thumbnail', self.default_thumbnail) != 'no_thumbnail' else (None, None)
        files.append(thumbnail_file)

        if author is not None:
            generic_embed.set_author(**author)
        if footer is not None:
            footer['text'] = f"{ZERO_WIDTH}\n" + footer['text'] + f"\n{ZERO_WIDTH}\n{ZERO_WIDTH}"
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

        _out = {"embed": generic_embed}
        files = [file_item for file_item in files if file_item is not None]
        if len(files) == 1:
            _out["file"] = files[0]
        elif len(files) > 1:
            _out['files'] = files

        return _out

    async def save_embed_as_json(self, embed, save_name: str = None):
        save_name = embed.title if save_name is None else save_name
        file_name = save_name.replace(' ', '_').replace('?', '').replace('!', '').replace('/', '').replace('"', '').replace("'", "").replace('*', '').replace('~', '').replace(ZERO_WIDTH, '').replace('\n', '').strip() + '.json'
        file_path = pathmaker(APPDATA["saved_embeds"], file_name)
        writejson(embed.to_dict(), file_path)

    async def make_static_embed(self, category, name):
        pass

    async def make_embed(self, typus, **kwargs):
        pass

    def collect_embed_build_recipes(self):
        self.embed_build_recipes = {}
        # for method_name, method_object in getmembers(self.__class__, iscoroutinefunction):
        for method_name, method_object in getmembers(self.__class__):
            if method_name.startswith('_embed_recipe_'):
                self.embed_build_recipes[method_name.replace("_embed_recipe_", "")] = getattr(self, method_name)

    @property
    def standard_embed_symbols(self):
        create_file(self.standard_embed_symbols_file)
        return loadjson(self.standard_embed_symbols_file)

    @property
    def folder_exists(self):
        return os.path.isdir(self.embed_data_folder)

    def _ensure_folder_exists(self):
        create_folder(self.embed_data_folder)

    @property
    def default_inline_value(self):
        """
        "default_inline_value": [true or false]
        """
        return loadjson(self.default_embed_data_file).get('default_inline_value')

    @property
    def default_title(self):
        """
        "default_title": ""
        replace template strings:   - $BOT_NAME$ for bot.display_name

        """

        _out = loadjson(self.default_embed_data_file).get('default_title')
        for replace_marker, replace_value in self.replacement_map.items():
            _out = _out.replace(replace_marker, replace_value)
        return _out

    @property
    def default_description(self):
        """
        "default_description": ""
        replace template strings:   - $BOT_NAME$ for bot.display_name
        """
        _out = loadjson(self.default_embed_data_file).get('default_description')
        for replace_marker, replace_value in self.replacement_map.items():
            _out = _out.replace(replace_marker, replace_value)
        return _out

    @property
    def default_author(self):
        """
        "default_author": {"name": "", "url": "", "icon_url": ""}
        """
        return loadjson(self.default_embed_data_file).get('default_author')

    @property
    def default_footer(self):
        """

        "default_footer": {"text": "", "icon_url": ""},

        """
        return loadjson(self.default_embed_data_file).get('default_footer')

    @property
    def default_thumbnail(self):
        """

        "default_thumbnail": ""

        """
        return loadjson(self.default_embed_data_file).get('default_thumbnail')

    @property
    def default_color(self):
        """
        "default_color": ""
        """
        return loadjson(self.default_embed_data_file).get('default_color')

    @property
    def default_timestamp(self):
        """
        optional!
        "default_timestamp": ""
        """
        return loadjson(self.default_embed_data_file).get('default_timestamp', datetime.now(tz=timezone("Europe/Berlin")))

    @property
    def default_type(self):
        """
        """
        return 'rich'

    async def if_ready(self):
        self.special_authors = {'bot_author': {'name': self.bot.display_name, 'url': self.bot.github_url, 'icon_url': self.bot.user.avatar_url},
                                'default_author': self.default_author}
        self.special_footers = {'feature_request_footer': {'text': "For feature suggestions and feature request, contact @Giddi".title(), "icon_url": self.bot.creator.member_object.avatar_url},
                                'default_footer': self.default_footer}
        self.replacement_map = {"$BOT_NAME$": self.bot.display_name}
        self.collect_embed_build_recipes()
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus):
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
