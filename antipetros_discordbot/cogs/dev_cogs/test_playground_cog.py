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
import subprocess
import platform
from tempfile import TemporaryDirectory
# * Third Party Imports -->
import discord
from discord.ext.commands import Greedy
from discord.utils import escape_markdown
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
from discord.ext import commands
from typing import Optional
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
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, writeit
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.misc import save_commands, async_load_json, image_to_url, color_hex_embed
from antipetros_discordbot.utility.checks import in_allowed_channels, has_attachments, allowed_channel_and_allowed_role_no_dm, is_not_giddi
from antipetros_discordbot.utility.regexes import DATE_REGEX, TIME_REGEX
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.converters import DateTimeFullConverter, DateOnlyConverter, FlagArg
from antipetros_discordbot.utility.discord_markdown_helper.the_dragon import THE_DRAGON

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

        figlet = Figlet(font='gothic', width=300)
        new_text = figlet.renderText(text.upper())
        await ctx.send(f"```fix\n{new_text}\n```")

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

    @commands.command(aliases=get_aliases("check_date_converter"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("test_playground", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("test_playground", 'allowed_channels')))
    async def check_date_converter(self, ctx, in_date: DateOnlyConverter):
        year = in_date.year
        month = in_date.month
        day = in_date.day
        hour = in_date.hour
        minute = in_date.minute
        second = in_date.second

        await ctx.send(f"__year:__ {year} | __month:__ {month} | __day:__ {day} || __hour:__ {hour} | __minute:__ {minute} | __second:__ {second}")

    @commands.command(aliases=get_aliases("check_template"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("test_playground", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("test_playground", 'allowed_channels')))
    @has_attachments(1)
    async def check_template(self, ctx):
        _file = ctx.message.attachments[0]
        if _file.filename.endswith('.sqf'):
            with ctx.typing():
                with TemporaryDirectory() as tempdir:
                    tempfile_path = pathmaker(tempdir, _file.filename)
                    await _file.save(tempfile_path)
                    cmd = subprocess.run([APPDATA["antistasi_template_checker.exe"], 'from_file', '-np', tempfile_path], check=True, capture_output=True)
                    _output = cmd.stdout.decode('utf-8', errors='replace')
                    print(_output)
                    await self.bot.split_to_messages(ctx, _output, in_codeblock=True)

    @commands.command(aliases=get_aliases("the_dragon") + ['the_wyvern'])
    @allowed_channel_and_allowed_role_no_dm("test_playground")
    async def the_dragon(self, ctx):
        await ctx.send(THE_DRAGON)

    @commands.command(aliases=get_aliases("random_embed_color"))
    @allowed_channel_and_allowed_role_no_dm("test_playground")
    async def random_embed_color(self, ctx):
        color = self.bot.command_staff.random_color
        embed = discord.Embed(title='test', description=color.name, color=color.int)
        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases("send_all_colors_file"))
    @allowed_channel_and_allowed_role_no_dm("test_playground")
    async def send_all_colors_file(self, ctx):
        _file = discord.File(str(self.bot.command_staff.all_colors_json_file), os.path.basename(str(self.bot.command_staff.all_colors_json_file)))
        await ctx.send('here', file=_file)

    @commands.command(aliases=get_aliases("send_all_colors_file"))
    @allowed_channel_and_allowed_role_no_dm("test_playground")
    async def check_flags(self, ctx, flags: Greedy[FlagArg(['make_embed', 'random_color'])], ending: str):
        print(flags)
        if 'make_embed' in flags:
            color = discord.Embed.Empty
            if 'random_color' in flags:
                color = self.bot.command_staff.random_color.int
            embed = discord.Embed(title='check flags', description=ending, color=color)
            await ctx.send(embed=embed)
        else:
            await ctx.send(ending)


# region [SpecialMethods]


    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

# endregion [SpecialMethods]


def setup(bot):
    bot.add_cog(TestPlaygroundCog(bot))
