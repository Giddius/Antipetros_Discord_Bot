"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random

# * Third Party Imports --------------------------------------------------------------------------------->
from discord import Color
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.exceptions import FuzzyMatchError
from antipetros_discordbot.utility.named_tuples import ColorItem
from antipetros_discordbot.utility.gidtools_functions import loadjson
from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

# ColorItem = namedtuple('ColorItem', ['name', 'hex', 'hex_alt', 'hsv', 'hsv_norm', 'int', 'rgb', 'rgb_norm', 'discord_color'])


class ColorKeeper(SubSupportBase):
    all_colors_json_file = APPDATA['all_color_list.json']
    base_colors_json_file = APPDATA['basic_color_list.json']

    def __init__(self, bot, support):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.colors = {}
        # MAYBE: create config file for subsupporter
        # MAYBE: specify if auto basic color attribute or not
        self._basic_colors_to_attribute()

        glog.class_init_notification(log, self)

    @property
    def color_item_list(self):
        return [item for name, item in self.colors.items()]

    def _basic_colors_to_attribute(self):
        basic_color_data = loadjson(self.base_colors_json_file)
        for color_name, color_data in basic_color_data.items():
            setattr(self, color_name.casefold(), self.dict_to_color_item(color_name, color_data))

    async def _make_color_items(self):
        for name, values in loadjson(self.all_colors_json_file).items():
            discord_color = Color.from_rgb(*values.get('rgb'))
            new_values = {}
            for key, data in values.items():
                if isinstance(data, list):
                    data = tuple(data)
                new_values[key] = data
            self.colors[name.casefold()] = ColorItem(name=name.casefold(), discord_color=discord_color, ** new_values)

    @staticmethod
    def dict_to_color_item(color_name, color_data):
        discord_color = Color.from_rgb(*color_data.get('rgb'))
        return ColorItem(name=color_name.casefold(), discord_color=discord_color, ** color_data)

    def color(self, color_name: str):
        return self.colors.get(color_name.casefold())

    def get_discord_color(self, color_name: str):
        color_name = color_name.casefold()
        if color_name == 'random':
            color_name = self.random_color
        if color_name in self.colors:
            return self.colors[color_name].discord_color
        scorer = fuzz.token_set_ratio
        fuzz_match = fuzzprocess.extractOne(color_name, [color for color in self.colors], scorer=scorer)
        if fuzz_match is None:
            raise FuzzyMatchError(color_name, scorer, data=[color for color in self.colors])
        return self.colors[fuzz_match[0]].discord_color

    @property
    def fake_colorless(self):
        return Color.from_rgb(54, 57, 63)

    @property
    def random_color(self):
        return random.choice(self.color_item_list)

    async def if_ready(self):
        await self._make_color_items()
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug("'%s' sub_support was UPDATED", str(self))

    def retire(self):
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return ColorKeeper
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
