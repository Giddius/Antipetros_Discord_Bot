

# region [Imports]

# * Standard Library Imports -->
import os
from io import BytesIO
from tempfile import TemporaryDirectory
from pathlib import Path
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
# * Third Party Imports -->
import discord
from PIL import Image, ImageEnhance
from discord.ext import commands


# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.enums import WATERMARK_COMBINATIONS, WatermarkPosition
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.misc import save_commands
from antipetros_discordbot.utility.checks import in_allowed_channels

from antipetros_discordbot.cogs import get_aliases
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_MANIPULATION_CONFIG_NAME = 'image_manipulation'

# endregion [Constants]

# TODO: create regions for this file
# TODO: Document and Docstrings


class ImageManipulatorCog(commands.Cog, command_attrs={'hidden': True, "name": "ImageManipulationCog"}):

    # region [ClassAttributes]

    allowed_stamp_formats = set(loadjson(APPDATA["image_file_extensions.json"]))
    stamp_positions = {'top': WatermarkPosition.Top, 'bottom': WatermarkPosition.Bottom, 'left': WatermarkPosition.Left, 'right': WatermarkPosition.Right, 'center': WatermarkPosition.Center}

# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.stamp_location = APPDATA['stamps']
        self.stamps = {}
        self.stamp_pos_functions = {WatermarkPosition.Right | WatermarkPosition.Bottom: self._to_bottom_right,
                                    WatermarkPosition.Right | WatermarkPosition.Top: self._to_top_right,
                                    WatermarkPosition.Right | WatermarkPosition.Center: self._to_center_right,
                                    WatermarkPosition.Left | WatermarkPosition.Bottom: self._to_bottom_left,
                                    WatermarkPosition.Left | WatermarkPosition.Top: self._to_top_left,
                                    WatermarkPosition.Left | WatermarkPosition.Center: self._to_center_left,
                                    WatermarkPosition.Center | WatermarkPosition.Center: self._to_center_center,
                                    WatermarkPosition.Center | WatermarkPosition.Bottom: self._to_bottom_center,
                                    WatermarkPosition.Center | WatermarkPosition.Top: self._to_top_center}

        self._get_stamps()
        if self.bot.is_debug:
            save_commands(self)
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]

    @property
    def allowed_channels(self):

        return set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels'))

    @property
    def target_stamp_fraction(self):

        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_fraction')

    @property
    def stamp_margin(self):

        return COGS_CONFIG.getint(IMAGE_MANIPULATION_CONFIG_NAME, 'stamps_margin')

    @property
    def stamp_opacity(self):
        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_opacity')

    @property
    def avatar_stamp_fraction(self):
        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'avatar_stamp_fraction')

    @property
    def avatar_stamp(self):
        return self._get_stamp_image(COGS_CONFIG.get(IMAGE_MANIPULATION_CONFIG_NAME, 'avatar_stamp').upper())

# endregion[Properties]

    def _get_stamps(self):
        self.stamps = {}
        for file in os.scandir(self.stamp_location):
            if os.path.isfile(file.path) is True and os.path.splitext(file.name)[1] in self.allowed_stamp_formats:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                self.stamps[name] = file.path

    def _get_stamp_image(self, stamp_name):
        image = Image.open(self.stamps.get(stamp_name))
        alpha = image.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(self.stamp_opacity)
        image.putalpha(alpha)
        return image.copy()

    @staticmethod
    def _stamp_resize(input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        input_image_width_fractioned = input_image_width * factor
        input_image_height_fractioned = input_image_height * factor
        transform_factor_width = input_image_width_fractioned / stamp_image.size[0]
        transform_factor_height = input_image_height_fractioned / stamp_image.size[1]
        transform_factor = (transform_factor_width + transform_factor_height) / 2
        return stamp_image.resize((round(stamp_image.size[0] * transform_factor), round(stamp_image.size[1] * transform_factor)), resample=Image.LANCZOS)

    def _to_bottom_right(self, input_image, stamp_image, factor):
        log.debug('pasting image to bottom_right')
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    def _to_top_right(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    def _to_center_right(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    def _to_bottom_left(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    def _to_top_left(self, input_image, stamp_image, factor):

        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    def _to_center_left(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    def _to_center_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    def _to_top_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    def _to_bottom_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = self._stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def _send_image(self, ctx, image, name, message_title, message_text=None, image_format=None, delete_after=None):
        image_format = 'png' if image_format is None else image_format
        with BytesIO() as image_binary:
            image.save(image_binary, image_format.upper(), optimize=True)
            image_binary.seek(0)
            out_file = discord.File(image_binary, filename=name + '.' + image_format)
            embed = discord.Embed(title=message_title, description=message_text)
            embed.set_thumbnail(url="https://userscontent2.emaze.com/images/20605779-4667-427c-a954-343bbc02a65f/c8b5d9a464d4288e9a951d3728772236.png")
            embed.set_image(url=f"attachment://{name.replace('_','')}.{image_format}")
            await ctx.send(embed=embed, file=out_file, delete_after=delete_after)

    @commands.command(aliases=get_aliases("stamp_image"))
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels')))
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def stamp_image(self, ctx, stamp: str = 'ASLOGO1', first_pos: str = 'bottom', second_pos: str = 'right', factor: float = None):
        async with ctx.channel.typing():
            if ctx.channel.name not in self.allowed_channels:
                return

            if len(ctx.message.attachments) == 0:
                # TODO: make as embed
                await ctx.send('! **there is NO image to antistasify** !')
                return
            if stamp not in self.stamps:
                # TODO: make as embed
                await ctx.send("! **There is NO stamp with that name** !")
                return
            first_pos = self.stamp_positions.get(first_pos.casefold(), None)
            second_pos = self.stamp_positions.get(second_pos.casefold(), None)

            if any(_pos is None for _pos in [first_pos, second_pos]) or first_pos | second_pos not in self.stamp_pos_functions:
                # TODO: make as embed
                await ctx.send("! **Those are NOT valid position combinations** !")
                return
            for _file in ctx.message.attachments:
                # TODO: maybe make extra attribute for input format, check what is possible and working. else make a generic format list
                if any(_file.filename.endswith(allowed_ext) for allowed_ext in self.allowed_stamp_formats):
                    _stamp = self._get_stamp_image(stamp)
                    _stamp = _stamp.copy()
                    with TemporaryDirectory(prefix='temp') as temp_dir:
                        temp_file = Path(pathmaker(temp_dir, 'temp_file.png'))
                        log.debug("Tempfile '%s' created", temp_file)
                        await _file.save(temp_file)
                        in_image = await self.bot.execute_in_thread(Image.open, temp_file)
                        in_image = await self.bot.execute_in_thread(in_image.copy)
                    factor = self.target_stamp_fraction if factor is None else factor
                    pos_function = self.stamp_pos_functions.get(first_pos | second_pos)

                    in_image = await self.bot.execute_in_thread(pos_function, in_image, _stamp, factor)
                    name = 'antistasified_' + os.path.splitext(_file.filename)[0]
                    # TODO: make as embed
                    await self._send_image(ctx, in_image, name, f"__**{name}**__")

    @commands.command(aliases=get_aliases("available_stamps"))
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels')))
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def available_stamps(self, ctx):

        await ctx.send(embed=await make_basic_embed(title="__**Currently available Stamps are:**__", footer="These messages will be deleted in 120 seconds", symbol='photo'), delete_after=120)
        for name, image_path in self.stamps.items():

            thumb_image = Image.open(image_path)
            thumb_image.thumbnail((128, 128))
            with BytesIO() as image_binary:
                thumb_image.save(image_binary, 'PNG', optimize=True)
                image_binary.seek(0)
                _file = discord.File(image_binary, filename=name + '.png')
                embed = discord.Embed(title="Available Stamp")
                embed.add_field(name='Stamp Name:', value=name)
                embed.set_image(url=f"attachment://{name}.png")
                await ctx.send(embed=embed, file=_file, delete_after=120)

    @commands.command(aliases=get_aliases("member_avatar"))
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_avatar_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels')))
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def other_members_avatar(self, ctx, members: commands.Greedy[discord.Member]):

        for member in members:
            avatar_image = await self.get_avatar_from_user(member)
            stamp = self.avatar_stamp
            modified_avatar = await self.bot.execute_in_thread(self._to_bottom_right, avatar_image, stamp, self.avatar_stamp_fraction)

            name = f"{member.name}_Member_avatar"
            await ctx.send(f"{member.name} hey!")
            await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**", f"__**{member.name}**__")

    async def get_avatar_from_user(self, user):
        avatar = user.avatar_url
        temp_dir = TemporaryDirectory()
        temp_file = pathmaker(temp_dir.name, 'user_avatar.png')
        log.debug("Tempfile '%s' created", temp_file)
        await avatar.save(temp_file)
        avatar_image = Image.open(temp_file)
        avatar_image = avatar_image.copy()
        avatar_image = avatar_image.convert('RGB')
        temp_dir.cleanup()
        return avatar_image


# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.qualified_name

# endregion[SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(ImageManipulatorCog(bot))
