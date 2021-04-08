

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from io import BytesIO
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter
from pytz import timezone
from discord.ext import commands, flags
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import make_config_name, alt_seconds_to_pretty
from antipetros_discordbot.utility.enums import WatermarkPosition
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester, log_invoker, has_attachments, owner_or_admin
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosFlagCommand, AntiPetrosBaseCommand
from antipetros_discordbot.utility.exceptions import ParameterError
from antipetros_discordbot.utility.image_manipulation import make_perfect_fontsize, find_min_fontsize, get_text_dimensions

# endregion[Imports]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings

# endregion [TODO]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))  # location of this file, does not work if app gets compiled to exe with pyinstaller
COG_NAME = "ImageManipulationCog"
CONFIG_NAME = make_config_name(COG_NAME)
get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion [Constants]


class ImageManipulatorCog(commands.Cog, command_attrs={'hidden': False, "name": COG_NAME}):
    """
    Commands that manipulate or generate images.
    """
    # region [ClassAttributes]

    config_name = CONFIG_NAME
    allowed_stamp_formats = set(loadjson(APPDATA["image_file_extensions.json"]))
    stamp_positions = {'top': WatermarkPosition.Top, 'bottom': WatermarkPosition.Bottom, 'left': WatermarkPosition.Left, 'right': WatermarkPosition.Right, 'center': WatermarkPosition.Center}
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.WORKING | CogState.OPEN_TODOS | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING,
                             "2021-02-06 05:09:20",
                             "f166431cb83ae36c91d70d7d09020e274a7ebea84d5a0c724819a3ecd2230b9eca0b3e14c2d473563d005671b7a2bf9d87f5449544eb9b57bcab615035b0f83d")}
    required_config_data = dedent("""  avatar_stamp = ASLOGO1
                                avatar_stamp_fraction = 0.2
                                stamps_margin = 5
                                stamp_fraction = 0.3""")
# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.stamp_location = APPDATA['stamps']
        self.stamps = {}
        self.nato_symbol_parts_location = APPDATA['nato_symbol_parts']
        self.nato_symbol_parts_images = {}
        self.stamp_pos_functions = {WatermarkPosition.Right | WatermarkPosition.Bottom: self._to_bottom_right,
                                    WatermarkPosition.Right | WatermarkPosition.Top: self._to_top_right,
                                    WatermarkPosition.Right | WatermarkPosition.Center: self._to_center_right,
                                    WatermarkPosition.Left | WatermarkPosition.Bottom: self._to_bottom_left,
                                    WatermarkPosition.Left | WatermarkPosition.Top: self._to_top_left,
                                    WatermarkPosition.Left | WatermarkPosition.Center: self._to_center_left,
                                    WatermarkPosition.Center | WatermarkPosition.Center: self._to_center_center,
                                    WatermarkPosition.Center | WatermarkPosition.Bottom: self._to_bottom_center,
                                    WatermarkPosition.Center | WatermarkPosition.Top: self._to_top_center}
        self.stamp_pos_functions_by_num = {'3': self._to_bottom_right,
                                           '9': self._to_top_right,
                                           '6': self._to_center_right,
                                           '1': self._to_bottom_left,
                                           '7': self._to_top_left,
                                           '4': self._to_center_left,
                                           '5': self._to_center_center,
                                           '2': self._to_bottom_center,
                                           '8': self._to_top_center}
        self.position_normalization_table = {'top': ['upper', 'above', 'up', 't', 'u'],
                                             'bottom': ['down', 'lower', 'b', 'base'],
                                             'center': ['middle', 'c', 'm'],
                                             'left': ['l'],
                                             'right': ['r']}
        # self.base_map_image = Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v3_2000_w_outposts.png")
        # self.outpost_overlay = {'city': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_city_marker.png"),
        #                         'volcano': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_volcano_marker.png"),
        #                         'airport': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_airport_marker.png")}
        self.old_map_message = None
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]

    async def on_ready_setup(self):
        self._get_stamps()
        self._get_nato_symbol_parts()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        self._get_stamps()
        log.debug('cog "%s" was updated', str(self))

# endregion[Setup]

# region [Properties]

    @property
    def target_stamp_fraction(self):

        return COGS_CONFIG.getfloat(CONFIG_NAME, 'stamp_fraction')

    @property
    def stamp_margin(self):

        return COGS_CONFIG.getint(CONFIG_NAME, 'stamps_margin')

    @property
    def avatar_stamp_fraction(self):
        return COGS_CONFIG.getfloat(CONFIG_NAME, 'avatar_stamp_fraction')

    @property
    def avatar_stamp(self):
        stamp_name = COGS_CONFIG.retrieve(CONFIG_NAME, 'avatar_stamp', direct_fallback='aslogo').upper()
        return self._get_stamp_image(stamp_name, 1)

    @property
    def fonts(self):
        fonts = {}
        for file in os.scandir(APPDATA['fonts']):
            if file.is_file() and file.name.endswith('ttf'):
                fonts[file.name.split('.')[0].casefold()] = pathmaker(file.path)
        return fonts


# endregion[Properties]

# region [Commands]


# endregion[Commands]

# region [HelperMethods]


# endregion[HelperMethods]

# region [Listener]


# endregion[Listener]


    def _get_nato_symbol_parts(self):
        self.nato_symbol_parts_images = {}
        for file in os.scandir(self.nato_symbol_parts_location):
            if os.path.isfile(file.path) is True:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                self.nato_symbol_parts_images[name] = file.path

    def _get_stamps(self):
        self.stamps = {}
        for file in os.scandir(self.stamp_location):
            if os.path.isfile(file.path) is True:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                self.stamps[name] = file.path

    def _get_stamp_image(self, stamp_name, stamp_opacity):
        stamp_name = stamp_name.upper()
        image = Image.open(self.stamps.get(stamp_name))
        alpha = image.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(stamp_opacity)
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
            file = discord.File(fp=image_binary, filename=name.replace('_', '') + '.' + image_format)
            embed = discord.Embed(title=message_title, description=message_text, color=self.support.cyan.discord_color, timestamp=datetime.now(tz=timezone("Europe/Berlin")), type='image')
            embed.set_author(name='AntiPetros', icon_url="https://www.der-buntspecht-shop.de/wp-content/uploads/Baumwollstoff-Camouflage-olivegruen-2.jpg")
            embed.set_image(url=f"attachment://{name.replace('_','')}.{image_format}")
            if delete_after is not None:
                embed.add_field(name='This Message will self destruct', value=f"in {alt_seconds_to_pretty(delete_after)}")
            await ctx.send(embed=embed, file=file, delete_after=delete_after)

    @flags.add_flag("--stamp-image", "-si", type=str, default='ASLOGO')
    @flags.add_flag("--first-pos", '-fp', type=str, default="bottom")
    @flags.add_flag("--second-pos", '-sp', type=str, default="right")
    @flags.add_flag("--stamp-opacity", '-so', type=float, default=1.0)
    @flags.add_flag('--factor', '-f', type=float, default=None)
    @auto_meta_info_command(enabled=get_command_enabled("stamp_image"), cls=AntiPetrosFlagCommand)
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def stamp_image(self, ctx, **flags):
        """
        Stamps an image with a small image from the available stamps.

        Needs to have the to stamp image as an attachment on the invoking message.

        Usefull for watermarking images.

        Get all available stamps with '@AntiPetros available_stamps'


        Example:
            @AntiPetros stamp_image -si ASLOGO -fp bottom -sp right -so 0.5 -f 0.25
        """
        async with ctx.channel.typing():

            if len(ctx.message.attachments) == 0:
                # TODO: make as embed
                await ctx.send('! **there is NO image to antistasify** !')
                return
            if flags.get('stamp_image') not in self.stamps:
                # TODO: make as embed
                await ctx.send("! **There is NO stamp with that name** !")
                return
            first_pos = self.stamp_positions.get(flags.get("first_pos").casefold(), None)
            second_pos = self.stamp_positions.get(flags.get("second_pos").casefold(), None)

            if any(_pos is None for _pos in [first_pos, second_pos]) or first_pos | second_pos not in self.stamp_pos_functions:
                # TODO: make as embed
                await ctx.send("! **Those are NOT valid position combinations** !")
                return
            for _file in ctx.message.attachments:
                # TODO: maybe make extra attribute for input format, check what is possible and working. else make a generic format list
                if any(_file.filename.endswith(allowed_ext) for allowed_ext in self.allowed_stamp_formats):
                    _stamp = self._get_stamp_image(flags.get('stamp_image'), flags.get('stamp_opacity'))
                    _stamp = _stamp.copy()
                    with TemporaryDirectory(prefix='temp') as temp_dir:
                        temp_file = Path(pathmaker(temp_dir, 'temp_file.png'))
                        log.debug("Tempfile '%s' created", temp_file)
                        await _file.save(temp_file)
                        in_image = await self.bot.execute_in_thread(Image.open, temp_file)
                        in_image = await self.bot.execute_in_thread(in_image.copy)
                    factor = self.target_stamp_fraction if flags.get('factor') is None else flags.get('factor')
                    pos_function = self.stamp_pos_functions.get(first_pos | second_pos)

                    in_image = await self.bot.execute_in_thread(pos_function, in_image, _stamp, factor)
                    name = 'antistasified_' + os.path.splitext(_file.filename)[0]
                    await ctx.message.delete()
                    # TODO: make as embed
                    await self._send_image(ctx, in_image, name, f"__**{name}**__")

    @auto_meta_info_command(enabled=get_command_enabled("available_stamps"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def available_stamps(self, ctx):
        """
        Posts all available stamps.

        Removes them after 2min to keep channel clean.

        Example:
            @AntiPetros available_stamps
        """
        await ctx.message.delete()
        await ctx.send(embed=await make_basic_embed(title="__**Currently available Stamps are:**__", footer="These messages will be deleted in 120 seconds", symbol='photo'), delete_after=120)
        for name, image_path in self.stamps.items():

            thumb_image = Image.open(image_path)
            thumb_image.thumbnail((128, 128))
            with BytesIO() as image_binary:
                await asyncio.sleep(0)
                thumb_image.save(image_binary, 'PNG', optimize=True)
                image_binary.seek(0)
                _file = discord.File(image_binary, filename=name + '.png')
                embed = discord.Embed(title="Available Stamp")
                embed.add_field(name='Stamp Name:', value=name)
                embed.set_image(url=f"attachment://{name}.png")
                await ctx.send(embed=embed, file=_file, delete_after=120)

    async def _member_avatar_helper(self, user: discord.Member, placement: callable, opacity: float):
        avatar_image = await self.get_avatar_from_user(user)
        stamp = self._get_stamp_image('ASLOGO', opacity)
        modified_avatar = await self.bot.execute_in_thread(placement, avatar_image, stamp, self.avatar_stamp_fraction)
        return modified_avatar

    @commands.group(case_insensitive=True)
    async def member_avatar(self, ctx):
        """
        Stamps the avatar of a Member with the Antistasi Crest.

        Returns the new stamped avatar as a .PNG image that the Member can save and replace his orginal avatar with.

        Example:
            @AntiPetros member_avatar
        """

    @member_avatar.command()
    @allowed_channel_and_allowed_role_2()
    async def for_discord(self, ctx):
        modified_avatar = await self._member_avatar_helper(ctx.author, self._to_center_center, 0.66)
        name = f"{ctx.author.name}_Member_avatar"
        await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**", delete_after=300)  # change completion line to "Pledge your allegiance to the Antistasi Rebellion!"?
        await ctx.message.delete()

    @member_avatar.command()
    async def for_github(self, ctx):
        modified_avatar = await self._member_avatar_helper(ctx.author, self._to_bottom_center, 1)
        name = f"{ctx.author.name}_Member_avatar"
        await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**", delete_after=300)  # change completion line to "Pledge your allegiance to the Antistasi Rebellion!"?
        await ctx.message.delete()

    @member_avatar.command()
    async def by_num(self, ctx, numberpad: str):
        if len(numberpad) > 1:
            await ctx.send('please only enter a single digit for numberpad position, please retry!')
            return
        if numberpad == '0':
            await ctx.send('0 is not a valid position, please try again!')
            return
        func = self.stamp_pos_functions_by_num.get(numberpad)
        modified_avatar = await self._member_avatar_helper(ctx.author, func, 1)
        name = f"{ctx.author.name}_Member_avatar"
        await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**", delete_after=300)  # change completion line to "Pledge your allegiance to the Antistasi Rebellion!"?
        await ctx.message.delete()

    async def _normalize_pos(self, pos: str):
        pos = pos.casefold()
        if pos not in self.position_normalization_table:
            for key, value in self.position_normalization_table.items():
                if pos in value:
                    return key
        raise ParameterError('image_position', pos)

    @member_avatar.command()
    async def by_place(self, ctx, first_pos: str, second_pos: str):
        first_pos = await self._normalize_pos(first_pos)
        second_pos = await self._normalize_pos(second_pos)
        func = self.stamp_pos_functions.get(self.stamp_positions.get(first_pos) | self.stamp_positions.get(second_pos))
        modified_avatar = await self._member_avatar_helper(ctx.author, func, 1)
        name = f"{ctx.author.name}_Member_avatar"
        await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**", delete_after=300)  # change completion line to "Pledge your allegiance to the Antistasi Rebellion!"?
        await ctx.message.delete()

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

    def map_image_handling(self, base_image, marker_name, color, bytes_out):
        log.debug("creating changed map, changed_location: '%s', changed_color: '%s'", marker_name, color)
        marker_image = self.outpost_overlay.get(marker_name)
        marker_alpha = marker_image.getchannel('A')
        marker_image = Image.new('RGBA', marker_image.size, color=color)
        marker_image.putalpha(marker_alpha)
        base_image.paste(marker_image, mask=marker_alpha)
        base_image.save(bytes_out, 'PNG', optimize=True)
        bytes_out.seek(0)
        return base_image, bytes_out

    @auto_meta_info_command(enabled=get_command_enabled('get_stamp_image'), aliases=["get_image"])
    @allowed_channel_and_allowed_role_2()
    async def get_stamp_image(self, ctx: commands.Context, image_name: str):
        image_name = image_name.split('.')[0].upper()
        if image_name not in self.stamps:
            await ctx.send(f"Don't have an image named `{image_name}` saved!", delete_after=120)
            return
        image = self.stamps.get(image_name)
        embed_data = await self.bot.make_generic_embed(title=image_name, description="Your requested image", thumbnail=None, image=image)
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(enabled=get_command_enabled('add_stamp'), aliases=["add_image"])
    @allowed_channel_and_allowed_role_2()
    @has_attachments(1)
    @log_invoker(log, "critical")
    async def add_stamp(self, ctx: commands.Context):
        """
        Adds a new stamp image to the available stamps.

        This command needs to have the image as an attachment.

        Example:
            @AntiPetros add_stamp
        """
        attachment = ctx.message.attachments[0]
        file_name = attachment.filename
        if file_name.casefold() in {file.casefold() for file in os.listdir(self.stamp_location)}:
            await ctx.reply(f"A Stamp file with the name `{file_name}` already exists, aborting!")
            return
        path = pathmaker(self.stamp_location, file_name)
        await attachment.save(path)
        stamp_name = file_name.split('.')[0].replace(' ', '_').strip().upper()
        await ctx.reply(f"successfully, saved new stamp. The stamp name to use is `{stamp_name}`")
        await self.bot.creator.member_object.send(f"New stamp was added by `{ctx.author.name}`", file=await attachment.to_file())
        self._get_stamps()

    def draw_text_line(self, image: Image, text_line: str, top_space: int, in_font: ImageFont.FreeTypeFont):
        width, height = image.size
        pfont = in_font
        draw = ImageDraw.Draw(image)
        w, h = draw.textsize(text_line, font=pfont)
        draw.text(((width - w) / 2, h + top_space), text_line, fill=(0, 0, 0), stroke_width=width // 150, stroke_fill=(50, 200, 25), font=pfont)

        return image, top_space + h + (height // 20)

    def draw_text_center(self, image: Image, text: str, in_font: ImageFont.FreeTypeFont):
        width, height = image.size
        pfont = in_font
        draw = ImageDraw.Draw(image)
        w, h = draw.textsize(text, font=pfont)
        draw.text(((width - w) / 2, (height - h) / 2), text, fill=(0, 0, 0), stroke_width=width // 150, stroke_fill=(204, 255, 204), font=pfont)

        return image

    @auto_meta_info_command(enabled=get_command_enabled('text_to_image'))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @has_attachments(1)
    async def text_to_image(self, ctx: commands.Context, font: str, *, text: str):
        mod_font_name = font.split('.')[0].casefold()
        if mod_font_name not in self.fonts:
            embed_data = await self.bot.make_generic_embed(title='Unkown Font', description=f"No font available with the name `{font}`.\nYou may have to add it via `@AntiPetros add_font`",
                                                           thumbnail="cancelled")
            await ctx.send(**embed_data, delete_after=120)
            return

        image_attachment = ctx.message.attachments[0]
        if image_attachment.filename.split('.')[-1].casefold() not in ['jpeg', 'png', 'jpg', 'tga']:
            embed_data = await self.bot.make_generic_embed(title="Wrong Image Format", description=f"Image need to be either `jpeg`, `png` or `tga` and not `{image_attachment.filename.split('.')[-1]}`",
                                                           thumbnail="cancelled")
            await ctx.send(**embed_data, delete_after=120)
            return

        with TemporaryDirectory() as tempdir:
            imagefilepath = pathmaker(tempdir, image_attachment.filename)
            await image_attachment.save(imagefilepath)
            base_image = Image.open(imagefilepath)
            base_image.load()
        width, height = base_image.size
        image_font = await self.bot.execute_in_thread(find_min_fontsize, self.fonts.get(mod_font_name), [line for line in text.splitlines() if line != ''], width, height)
        top_space = 0
        for line in text.splitlines():
            if line == '':
                top_space += ((height // 20) * 2)
            else:
                base_image, top_space = await self.bot.execute_in_thread(self.draw_text_line, base_image, line, top_space, image_font)
        await self._send_image(ctx, base_image, image_attachment.filename.split('.')[0] + '_with_text.png', "Modified Image", message_text="Here is your image with pasted Text", image_format='png')

    @auto_meta_info_command(enabled=get_command_enabled('add_font'))
    @owner_or_admin()
    @has_attachments(1)
    async def add_font(self, ctx: commands.Context):
        font_attachment = ctx.message.attachments[0]
        if font_attachment.filename.split('.')[-1] != 'ttf':
            embed_data = await self.bot.make_generic_embed(title='Wrong input filetype', description=f"Attachment has to be a Truetype Font (extension: `.ttf`) and not `.{font_attachment.filename.split('.')[-1]}`",
                                                           thumbnail="not_possible")
            await ctx.send(**embed_data, delete_after=120)
            return
        new_path = pathmaker(APPDATA['fonts'], font_attachment.filename)
        await font_attachment.save(new_path)
        embed_data = await self.bot.make_generic_embed(title="Added new Font", description=f"Font `{font_attachment.filename}` was successfully saved!",
                                                       thumbnail="save")
        await ctx.send(**embed_data, delete_after=300)

    async def _make_font_preview(self, font_name, font_path):
        b_image = Image.new('RGBA', (512, 512), color=(256, 256, 256, 0))
        image_font = await self.bot.execute_in_thread(make_perfect_fontsize, font_path, font_name, 512, 512)
        preview_image = await self.bot.execute_in_thread(self.draw_text_center, b_image, font_name, image_font)
        return preview_image

    @auto_meta_info_command(enabled=get_command_enabled('add_font'))
    @allowed_channel_and_allowed_role_2()
    async def list_fonts(self, ctx: commands.Context):
        embed = discord.Embed(title="Available Fonts")
        await ctx.send(embed=embed, delete_after=60)
        for font_name, font_path in self.fonts.items():

            embed_data = await self.bot.make_generic_embed(title=font_name, image=await self._make_font_preview(font_name, font_path), thumbnail=None)
            await ctx.send(**embed_data, delete_after=60)

        await asyncio.sleep(60)
        await ctx.message.delete()

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

# endregion[SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(ImageManipulatorCog(bot)))
