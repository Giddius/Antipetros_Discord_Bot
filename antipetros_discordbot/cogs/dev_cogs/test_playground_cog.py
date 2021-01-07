# * Standard Library Imports -->
import os
import random
import statistics
from io import BytesIO
from time import time
import pickle
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import random
import asyncio
import platform
# * Third Party Imports -->
import discord
from discord.utils import escape_markdown
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
from discord.ext import commands
from fuzzywuzzy import process as fuzzprocess
import gidlogger as glog
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googletrans import Translator, LANGUAGES
from fuzzywuzzy import process as fuzzprocess
from fuzzywuzzy import fuzz
from pyfiglet import Figlet
# * Local Imports -->

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import Bold, Cursive, CodeBlock, LineCode, UnderScore, BlockQuote
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.misc import save_commands, async_load_json, image_to_url, color_hex_embed
from antipetros_discordbot.utility.checks import in_allowed_channels
from antipetros_discordbot.utility.regexes import DATE_REGEX, TIME_REGEX
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.cogs import get_aliases

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]


APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

HELP_TEST_DATA = loadjson(APPDATA["command_help.json"])


FAQ_THING = """**FAQ No 17**
_How to become a server member?_
_Read the channel description on teamspeak or below_

_**Becoming a member:**_
```
Joining our ranks is simple: play with us and participate in this community! If the members like you you may be granted trial membership by an admin upon recommendation.

Your contribution and participation to this community will determine how long the trial period will be, and whether or not it results in full membership. As a trial member, you will receive in-game membership and a [trial] tag on these forums which assures you an invite to all events including official member meetings. Do note that only full members are entitled to vote on issues at meetings.
```"""


class TestPlaygroundCog(commands.Cog, command_attrs={'hidden': True, "name": "TestPlayground"}):
    config_name = "test_playground"
    language_dict = {value: key for key, value in LANGUAGES.items()}

    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = set(COGS_CONFIG.getlist('test_playground', 'allowed_channels'))

    @commands.command(aliases=get_aliases("make_figlet"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("test_playground", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("test_playground", 'allowed_channels')))
    async def make_figlet(self, ctx, *, text: str):
        for _ in range(3):
            await ctx.send('#' * 25)
            await asyncio.sleep(1)
        for font in loadjson('figlet_fonts.json'):
            figlet = Figlet(font=font, width=300)
            new_text = figlet.renderText(text.upper())
            await ctx.send(f"**{font}**\n{ZERO_WIDTH}\n```fix\n{new_text}\n```\n{ZERO_WIDTH}")

            await asyncio.sleep(2.5)

    async def get_text_dimensions(self, text_string, font_name, image_size):
        # https://stackoverflow.com/a/46220683/9263761
        font_size = 500
        buffer = 50
        image_width, image_height = image_size
        image_width = image_width - (buffer * 2)
        image_height = image_height - (buffer * 2)

        text_width = 999999999
        text_height = 99999999
        while text_width > image_width or text_height > image_height:
            font = ImageFont.truetype(font_name, font_size)
            ascent, descent = font.getmetrics()

            text_width = font.getmask(text_string).getbbox()[2]
            text_height = font.getmask(text_string).getbbox()[3] + descent
            font_size -= 1
        return font, text_width, text_height, font_size

    async def get_smalle_text_dimensions(self, text_string, font):
        # https://stackoverflow.com/a/46220683/9263761
        ascent, descent = font.getmetrics()

        text_width = font.getmask(text_string).getbbox()[2]
        text_height = font.getmask(text_string).getbbox()[3] + descent

        return (text_width, text_height)

    async def get_font_path(self, font_name):
        _font_dict = {}
        font_folder = pathmaker() if platform.system() == 'Windows' else None
        if font_folder is None:
            raise FileNotFoundError("could not locate font folder")
        for file in os.scandir(font_folder):
            if file.is_file() and file.name.endswith('.ttf'):
                _font_dict[os.path.splitext(file.name)[0].casefold()] = pathmaker(file.path)
        if font_name.casefold() in _font_dict:
            return _font_dict.get(font_name.casefold())
        new_font_name = fuzzprocess.extractOne(font_name.casefold(), _font_dict.keys())
        return _font_dict.get(new_font_name)

    @commands.command(aliases=get_aliases("text_to_image"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("test_playground", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("test_playground", 'allowed_channels')))
    async def text_to_image(self, ctx, *, text: str):
        font_path = 'stencilla.ttf'
        image_path = APPDATA['armaimage.png']
        print(image_path)

        image = Image.open(APPDATA['armaimage.png'])
        font, text_width, text_height, font_size = await self.get_text_dimensions(text, font_path, image.size)
        second_font = ImageFont.truetype(font_path, size=font_size - (font_size // 35))
        second_width, second_height = await self.get_smalle_text_dimensions(text, second_font)
        draw_interface = ImageDraw.Draw(image, mode='RGBA')
        draw_interface.text((((image.size[0] - text_width) // 2), 50), text, fill=(1, 1, 1), font=font)
        draw_interface.text((((image.size[0] - second_width) // 2), 50 + 10), text, fill=(255, 226, 0), font=second_font, stroke_fill=(0, 176, 172), stroke_width=(font_size // 50))
        await self._send_image(ctx, image, 'test', 'TEST', 'PNG')

    async def _send_image(self, ctx, image, name, message_title, image_format=None, delete_after=None):
        image_format = 'png' if image_format is None else image_format
        with BytesIO() as image_binary:
            image.save(image_binary, image_format.upper(), optimize=True)
            image_binary.seek(0)
            out_file = discord.File(image_binary, filename=name + '.' + image_format)
            embed = discord.Embed(title=message_title)
            embed.set_image(url=f"attachment://{name.replace('_','')}.{image_format}")
            await ctx.send(embed=embed, file=out_file, delete_after=delete_after)

        # region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

# endregion [SpecialMethods]


def setup(bot):
    bot.add_cog(TestPlaygroundCog(bot))
