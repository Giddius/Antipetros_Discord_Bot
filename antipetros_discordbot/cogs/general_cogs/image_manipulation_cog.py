

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from io import BytesIO
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from PIL import Image, ImageEnhance, ImageFont, ImageDraw
from pytz import timezone
from discord.ext import flags, tasks, commands
from fuzzywuzzy import fuzz, process as fuzzprocess
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import save_commands, make_config_name
from antipetros_discordbot.utility.enums import WatermarkPosition
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
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
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
COG_NAME = "ImageManipulationCog"
CONFIG_NAME = make_config_name(COG_NAME)
get_command_enabled = command_enabled_checker(CONFIG_NAME)
# endregion [Constants]


class ImageManipulatorCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Soon
    """
    # region [ClassAttributes]
    config_name = CONFIG_NAME
    allowed_stamp_formats = set(loadjson(APPDATA["image_file_extensions.json"]))
    stamp_positions = {'top': WatermarkPosition.Top, 'bottom': WatermarkPosition.Bottom, 'left': WatermarkPosition.Left, 'right': WatermarkPosition.Right, 'center': WatermarkPosition.Center}
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.WORKING | CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING,
                             "2021-02-06 05:09:20",
                             "f166431cb83ae36c91d70d7d09020e274a7ebea84d5a0c724819a3ecd2230b9eca0b3e14c2d473563d005671b7a2bf9d87f5449544eb9b57bcab615035b0f83d")}
    required_config_data = """"""
# endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
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
        self.base_map_image = Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v3_2000_w_outposts.png")
        self.outpost_overlay = {'city': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_city_marker.png"),
                                'volcano': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_volcano_marker.png"),
                                'airport': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_airport_marker.png")}
        self.old_map_message = None
        self._get_stamps()
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Setup]


    async def on_ready_setup(self):
        self._get_stamps()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
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
        return self._get_stamp_image(COGS_CONFIG.get(CONFIG_NAME, 'avatar_stamp').upper())

# endregion[Properties]

    def _get_stamps(self):
        self.stamps = {}
        for file in os.scandir(self.stamp_location):
            if os.path.isfile(file.path) is True and os.path.splitext(file.name)[1] in self.allowed_stamp_formats:
                name = file.name.split('.')[0].replace(' ', '_').strip().upper()
                self.stamps[name] = file.path

    def _get_stamp_image(self, stamp_name, stamp_opacity):
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
            await ctx.send(embed=embed, file=file, delete_after=delete_after)

    @flags.add_flag("--stamp-image", "-si", type=str, default='ASLOGO1')
    @flags.add_flag("--first-pos", '-fp', type=str, default="bottom")
    @flags.add_flag("--second-pos", '-sp', type=str, default="right")
    @flags.add_flag("--stamp-opacity", '-so', type=float, default=1.0)
    @flags.add_flag('--factor', '-f', type=float, default=None)
    @commands.command(aliases=get_aliases("stamp_image"), enabled=get_command_enabled("stamp_image"), cls=flags.FlagCommand)
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def stamp_image(self, ctx, **flags):
        """
        Stamps an image with a small image from the available stamps.

        Usefull for watermarking images.

        Get all available stamps with '@AntiPetros available_stamps'

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

    @commands.command(aliases=get_aliases("available_stamps"), enabled=get_command_enabled("available_stamps"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def available_stamps(self, ctx):
        """
        Posts all available stamps.

        """
        await ctx.message.delete()
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

    @commands.command(aliases=get_aliases("member_avatar"), enabled=get_command_enabled("member_avatar"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def member_avatar(self, ctx):
        """
        Stamps the avatar of a Member with the Antistasi Crest.

        Returns the new stamped avatar as image, that the Member can save and replace his orginal avatar with.

        """
        avatar_image = await self.get_avatar_from_user(ctx.author)
        stamp = self.avatar_stamp
        modified_avatar = await self.bot.execute_in_thread(self._to_bottom_right, avatar_image, stamp, self.avatar_stamp_fraction)

        name = f"{ctx.author.name}_Member_avatar"
        await self._send_image(ctx, modified_avatar, name, "**Your New Avatar**")

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

    @commands.command(aliases=get_aliases("map_changed"), enabled=get_command_enabled("map_changed"))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=False)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def map_changed(self, ctx, marker, color):
        """
        Proof of concept for future real time server map.
        """
        log.info("command was initiated by '%s'", ctx.author.name)
        with BytesIO() as image_binary:

            self.base_map_image, image_binary = await self.bot.execute_in_thread(self.map_image_handling, self.base_map_image, marker, color, image_binary)

            if self.old_map_message is not None:
                await self.old_map_message.delete()
            delete_time = None
            embed = discord.Embed(title='Current Server Map State', color=self.support.green.discord_color, timestamp=datetime.now(tz=timezone("Europe/Berlin")), type="image")
            embed.set_author(name='Antistasi Community Server 1', icon_url="https://s3.amazonaws.com/files.enjin.com/1218665/site_logo/NEW%20LOGO%20BANNER.png", url="https://a3antistasi.enjin.com/")
            embed.set_image(url="attachment://map.png")
            self.old_map_message = await ctx.send(embed=embed, file=discord.File(fp=image_binary, filename="map.png"), delete_after=delete_time)

        log.debug("finished 'map_changed' command")


# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

# endregion[SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(ImageManipulatorCog(bot)))
