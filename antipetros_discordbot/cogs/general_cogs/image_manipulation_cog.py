
__updated__ = '2020-11-28 02:53:59'

# region [Imports]

# * Standard Library Imports -->
import os
from io import BytesIO

# * Third Party Imports -->
import discord
from PIL import Image, ImageEnhance
from discord.ext import commands

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.enums import WATERMARK_COMBINATIONS, WatermarkPosition
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.data.config.config_singleton import COGS_CONFIG

# endregion[Imports]

# region [Logging]

log = glog.aux_logger(__name__)
log.debug(glog.imported(__name__))

# endregion[Logging]

# region [Constants]

# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_MANIPULATION_CONFIG_NAME = 'image_manipulation'

# endregion [Constants]


class ImageManipulator(commands.Cog):
    allowed_stamp_formats = set(loadjson(pathmaker(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\data\data_storage\json_data\image_file_extensions.json")))
    stamp_positions = {'top': WatermarkPosition.Top, 'bottom': WatermarkPosition.Bottom, 'left': WatermarkPosition.Left, 'right': WatermarkPosition.Right, 'center': WatermarkPosition.Center}

    def __init__(self, bot):
        self.bot = bot
        self.stamp_location = pathmaker(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\antipetros_discordbot\data\data_storage\images\stamps")
        self.stamps = {}
        self.allowed_channels = set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels'))
        self.target_stamp_fraction = COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_fraction')
        self.stamp_margin = COGS_CONFIG.getint(IMAGE_MANIPULATION_CONFIG_NAME, 'stamps_margin')
        self.stamp_opacity = COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_opacity')
        self.stamp_pos_functions = {WatermarkPosition.Right | WatermarkPosition.Bottom: self.to_bottom_right,
                                    WatermarkPosition.Right | WatermarkPosition.Top: self.to_top_right,
                                    WatermarkPosition.Right | WatermarkPosition.Center: self.to_center_right,
                                    WatermarkPosition.Left | WatermarkPosition.Bottom: self.to_bottom_left,
                                    WatermarkPosition.Left | WatermarkPosition.Top: self.to_top_left,
                                    WatermarkPosition.Left | WatermarkPosition.Center: self.to_center_left,
                                    WatermarkPosition.Center | WatermarkPosition.Center: self.to_center_center,
                                    WatermarkPosition.Center | WatermarkPosition.Bottom: self.to_bottom_center,
                                    WatermarkPosition.Center | WatermarkPosition.Top: self.to_top_center}
        self.get_stamps()

    def get_stamps(self):
        self.stamps = {}
        for file in os.scandir(self.stamp_location):
            if os.path.isfile(file.path) is True and os.path.splitext(file.name)[1] in self.allowed_stamp_formats:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                image = Image.open(file.path)
                alpha = image.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(self.stamp_opacity)
                image.putalpha(alpha)
                self.stamps[name] = image

    async def stamp_resize(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        input_image_width_fractioned = input_image_width * factor
        input_image_height_fractioned = input_image_height * factor
        transform_factor_width = input_image_width_fractioned / stamp_image.size[0]
        transform_factor_height = input_image_height_fractioned / stamp_image.size[1]
        transform_factor = (transform_factor_width + transform_factor_height) / 2
        return stamp_image.resize((round(stamp_image.size[0] * transform_factor), round(stamp_image.size[1] * transform_factor)), resample=Image.LANCZOS)

    async def to_bottom_right(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def to_top_right(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def to_center_right(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (input_image_width - _resized_stamp.size[0] - self.stamp_margin, round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    async def to_bottom_left(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def to_top_left(self, input_image, stamp_image, factor):

        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def to_center_left(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (0 + self.stamp_margin, round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    async def to_center_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), round((input_image_height / 2) - (_resized_stamp.size[1] / 2))),
                          _resized_stamp)
        return input_image

    async def to_top_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), 0 + self.stamp_margin),
                          _resized_stamp)
        return input_image

    async def to_bottom_center(self, input_image, stamp_image, factor):
        input_image_width, input_image_height = input_image.size
        _resized_stamp = await self.stamp_resize(input_image, stamp_image, factor)
        input_image.paste(_resized_stamp,
                          (round((input_image_width / 2) - (_resized_stamp.size[0] / 2)), input_image_height - _resized_stamp.size[1] - self.stamp_margin),
                          _resized_stamp)
        return input_image

    @commands.command(name='antistasify')
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    async def stamp_image(self, ctx, stamp='AS_LOGO_1', first_pos='bottom', second_pos='right', factor: float = None):
        if ctx.channel.name not in self.allowed_channels:
            return
        if len(ctx.message.attachments) == 0:
            await ctx.send('! **there is NO image to antistasify** !')
            return
        if stamp not in self.stamps:
            await ctx.send("! **There is NO stamp with that name** !")
            return
        first_pos = self.stamp_positions.get(first_pos.casefold(), None)
        second_pos = self.stamp_positions.get(second_pos.casefold(), None)

        if any(_pos is None for _pos in [first_pos, second_pos]) or first_pos | second_pos not in self.stamp_pos_functions:
            await ctx.send("! **Those are NOT valid position combinations** !")
            return
        for _file in ctx.message.attachments:
            # TODO: maybe make extra attribute for input format, check what is possible and working. else make a generic format list
            if any(_file.filename.endswith(allowed_ext) for allowed_ext in self.allowed_stamp_formats):
                _stamp = self.stamps.get(stamp).copy()
                _as_file = await _file.to_file()
                in_image = Image.open(_as_file.fp)
                factor = self.target_stamp_fraction if factor is None else factor
                in_image = await self.stamp_pos_functions.get(first_pos | second_pos)(in_image, _stamp, factor)
                with BytesIO() as image_binary:
                    in_image.save(image_binary, 'PNG', optimize=True)
                    image_binary.seek(0)
                    name = 'antistasified_' + os.path.splitext(_file.filename)[0] + '.png'
                    out_file = discord.File(image_binary, filename=name)
                    await ctx.send(f"__**{name}**__", file=out_file)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    async def flag_test(self, ctx, flag_one, flag_two):
        if ctx.channel.name not in self.allowed_channels:
            return
        _flag_one = self.stamp_positions.get(flag_one.casefold(), None)
        _flag_two = self.stamp_positions.get(flag_two.casefold(), None)
        _comb = _flag_one | _flag_two
        if _comb in WATERMARK_COMBINATIONS:
            await ctx.send(f"{str(_comb)} is a valid combination")
        else:
            await ctx.send(f"{str(_comb)} is NOT a valid combination!")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    async def available_stamps(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return

        await ctx.send("__**Currently available Stamps are:**__\nThese messages will be deleted in 120 seconds", delete_after=120)
        for name, image in self.stamps.items():
            thumb_image = image.copy()
            thumb_image.thumbnail((128, 128))
            with BytesIO() as image_binary:
                thumb_image.save(image_binary, 'PNG', optimize=True)
                image_binary.seek(0)
                _file = discord.File(image_binary, filename=name + '.png')
                await ctx.send(name, file=_file, delete_after=120)

    @commands.Cog.listener(name='on_ready')
    async def extra_cog_setup(self):
        log.info(f"{self} Cog ----> finished extra setup")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    bot.add_cog(ImageManipulator(bot))