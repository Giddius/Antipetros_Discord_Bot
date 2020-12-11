

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


class ImageManipulator(commands.Cog, command_attrs={'hidden': True}):

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
            self.save_commands()
        glog.class_init_notification(log, self)

    def save_commands(self):
        command_json_file = r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\docs\commands.json"
        command_json = loadjson(command_json_file)
        command_json[str(self)] = {'file_path': pathmaker(os.path.abspath(__file__)),
                                   'description': __doc__,
                                   'commands': {(com.name + ' ' + com.signature).replace('<ctx>', '').replace('  ', ' ').strip(): com.help for com in self.get_commands()}}
        writejson(command_json, command_json_file, indent=4)
        log.debug("commands for %s saved to %s", self, command_json_file)

# endregion[Init]

# region [Properties]

    @property
    def allowed_channels(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return set(COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_channels'))

    @property
    def target_stamp_fraction(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_fraction')

    @property
    def stamp_margin(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return COGS_CONFIG.getint(IMAGE_MANIPULATION_CONFIG_NAME, 'stamps_margin')

    @property
    def stamp_opacity(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'stamp_opacity')

    @property
    def avatar_stamp_fraction(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return COGS_CONFIG.getfloat(IMAGE_MANIPULATION_CONFIG_NAME, 'avatar_stamp_fraction')

    @property
    def avatar_stamp(self):
        if self.bot.is_debug:
            COGS_CONFIG.read()
        return self.stamps.get(COGS_CONFIG.get(IMAGE_MANIPULATION_CONFIG_NAME, 'avatar_stamp')).copy()

# endregion[Properties]

    def _get_stamps(self):
        self.stamps = {}
        for file in os.scandir(self.stamp_location):
            if os.path.isfile(file.path) is True and os.path.splitext(file.name)[1] in self.allowed_stamp_formats:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                image = Image.open(file.path)
                alpha = image.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(self.stamp_opacity)
                image.putalpha(alpha)
                self.stamps[name] = image

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

    async def _send_image(self, ctx, image, name, message_title, image_format=None):
        image_format = 'png' if image_format is None else image_format
        with BytesIO() as image_binary:
            image.save(image_binary, image_format.upper(), optimize=True)
            image_binary.seek(0)
            out_file = discord.File(image_binary, filename=name + '.' + image_format)
            embed = discord.Embed(title=message_title)
            embed.set_image(url=f"attachment://{name.replace('_','')}.{image_format}")
            await ctx.send(embed=embed, file=out_file)

    @commands.command(name='antistasify')
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def stamp_image(self, ctx, stamp='ASLOGO1', first_pos='bottom', second_pos='right', factor: float = None):
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
                    _stamp = self.stamps.get(stamp).copy()
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
            await self.bot.did_command()

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_roles'))
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def available_stamps(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return

        await ctx.send(embed=await self.bot.make_basic_embed(title="__**Currently available Stamps are:**__", footer="These messages will be deleted in 120 seconds", symbol='photo'), delete_after=120)
        for name, image in self.stamps.items():
            thumb_image = image.copy()
            thumb_image.thumbnail((128, 128))
            with BytesIO() as image_binary:
                thumb_image.save(image_binary, 'PNG', optimize=True)
                image_binary.seek(0)
                _file = discord.File(image_binary, filename=name + '.png')
                embed = discord.Embed(title="Available Stamp")
                embed.add_field(name='Stamp Name:', value=name)
                embed.set_image(url=f"attachment://{name}.png")
                await ctx.send(embed=embed, file=_file, delete_after=120)
        await self.bot.did_command()

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist(IMAGE_MANIPULATION_CONFIG_NAME, 'allowed_avatar_roles'))
    @commands.cooldown(1, 60 * 5, commands.BucketType.member)
    async def member_avatar(self, ctx, target_id: int = None):
        if ctx.channel.name not in self.allowed_channels:
            return
        if target_id is None:
            avatar_image = await self.get_avatar_from_user(ctx.author)
        else:
            guild_id = ctx.guild.id
            user = await self.bot.retrieve_member(guild_id, target_id)
            avatar_image = await self.get_avatar_from_user(user)
        stamp = self.avatar_stamp
        modified_avatar = await self.bot.execute_in_thread(self._to_bottom_right, avatar_image, stamp, self.avatar_stamp_fraction)

        name = f"{ctx.author.name}_Member_avatar"

        await self._send_image(ctx, modified_avatar, name, f"**Your New Avatar {ctx.author.name}**")
        await self.bot.did_command()

    async def get_avatar_from_user(self, user):
        avatar = user.avatar_url
        with TemporaryDirectory(prefix='temp') as temp_dir:
            temp_file = Path(pathmaker(temp_dir, 'temp_file.png'))
            log.debug("Tempfile '%s' created", temp_file)
            await avatar.save(temp_file)
            avatar_image = await self.bot.execute_in_thread(Image.open, temp_file)
            avatar_image = avatar_image.copy()
        return avatar_image


# region [SpecialMethods]


    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

# endregion[SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(ImageManipulator(bot))
