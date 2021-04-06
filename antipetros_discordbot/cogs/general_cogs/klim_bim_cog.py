
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from math import ceil
import secrets
import asyncio
from urllib.parse import quote as urlquote
from textwrap import dedent
from functools import reduce
from io import BytesIO
import re
from typing import Optional
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
from icecream import ic
from discord import AllowedMentions
from pyfiglet import Figlet
from PIL import Image, ImageDraw, ImageFont
import discord

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.misc import is_even, make_config_name
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.the_dragon import THE_DRAGON
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState, UpdateTypus
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.gidtools_functions import bytes2human
from antipetros_discordbot.utility.exceptions import ParseDiceLineError
from antipetros_discordbot.utility.id_generation import make_full_cog_id
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
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

COG_NAME = "KlimBimCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class KlimBimCog(commands.Cog, command_attrs={'hidden': False, "name": COG_NAME}):
    """
    Collection of small commands that either don't fit anywhere else or are just for fun.
    """
    # region [ClassAttributes]
    cog_id = 12
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.WORKING,
                             "2021-02-06 03:32:39",
                             "05703df4faf098a7f3f5cea49c51374b3225162318b081075eb0745cc36ddea6ff11d2f4afae1ac706191e8db881e005104ddabe5ba80687ac239ede160c3178")}

    required_config_data = dedent("""
                                        coin_image_heads = https://i.postimg.cc/XY4fhCf5/antipetros-coin-head.png,
                                        coin_image_tails = https://i.postimg.cc/HsQ0B2yH/antipetros-coin-tails.png""")
    dice_statement_regex = re.compile(r"(?P<amount>\d+)(?P<dice_type>d\d+)", re.IGNORECASE)
    # endregion [ClassAttributes]

    # region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.dice_mapping = {
            'd4': {'sides': 4},
            'd6': {'sides': 6},
            'd8': {'sides': 8},
            'd10': {'sides': 10},
            'd12': {'sides': 12},
            'd20': {'sides': 20},
            'd100': {'sides': 100}
        }
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    @ auto_meta_info_command(enabled=get_command_enabled('the_dragon'))
    @ allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def the_dragon(self, ctx):
        """
        Posts and awesome ASCII Art Dragon!

        Example:
            @AntiPetros the_dragon

        """
        suprise_dragon_check = secrets.randbelow(100) + 1
        if suprise_dragon_check == 1:
            await ctx.send('https://i.redd.it/073kp5pr5ev11.jpg')
        elif suprise_dragon_check == 2:
            await ctx.send('https://www.sciencenewsforstudents.org/wp-content/uploads/2019/11/860-dragon-header-iStock-494839519.gif')
        else:
            await ctx.send(THE_DRAGON)

    @ auto_meta_info_command(enabled=get_command_enabled('flip_coin'))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def flip_coin(self, ctx: commands.Context, only_text: str = None):
        """
        Simulates a coin flip and posts the result as an image of a Petros Dollar.

        Example:
            @AntiPetros flip_coin

        """
        with ctx.typing():

            result = (secrets.randbelow(2) + 1)
            coin = "heads" if is_even(result) is True else 'tails'
            color = "green" if coin == "heads" else "red"
            await asyncio.sleep(random.random() * random.randint(1, 2))

            coin_image = COGS_CONFIG.retrieve(self.config_name, f"coin_image_{coin}", typus=str)
            nato_check_num = secrets.randbelow(100) + 1
            if nato_check_num <= 1:
                coin = 'nato, you lose!'
                coin_image = "https://i.postimg.cc/cdL5Z0BH/nato-coin.png"
                color = "blue"
            if only_text is not None and only_text.casefold() == "text":
                embed = discord.Embed(description=f"{ctx.author.mention} flipped a Coin: **{coin.title()}**", color=self.bot.get_discord_color(color))
                await ctx.reply(embed=embed, allowed_mentions=AllowedMentions.none())
            else:
                embed = await self.bot.make_generic_embed(title=coin.title(), description=ZERO_WIDTH, image=coin_image, thumbnail='no_thumbnail', color=color)

                await ctx.reply(**embed, allowed_mentions=AllowedMentions.none())
            return coin

    @ auto_meta_info_command(enabled=get_command_enabled('urban_dictionary'))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def urban_dictionary(self, ctx, term: str, entries: int = 1):
        """
        Searches Urbandictionary for the search term and post the answer as embed

        Args:

            term (str): the search term
            entries (int, optional): How many UD entries for that term it should post, max is 5. Defaults to 1.

        Example:
            @AntiPetros urban_dictionary Petros 2

        """
        if entries > 5:
            await ctx.send('To many requested entries,max allowed return entries is 5')
            return

        urban_request_url = "https://api.urbandictionary.com/v0/define?term="
        full_url = urban_request_url + urlquote(term)
        async with self.bot.aio_request_session.get(full_url) as _response:
            if RequestStatus(_response.status) is RequestStatus.Ok:
                json_content = await _response.json()
                content_list = sorted(json_content.get('list'), key=lambda x: x.get('thumbs_up') + x.get('thumbs_down'), reverse=True)

                for index, item in enumerate(content_list):
                    if index <= entries - 1:
                        _embed_data = await self.bot.make_generic_embed(title=f"Definition for '{item.get('word')}'",
                                                                        description=item.get('definition').replace('[', '*').replace(']', '*'),
                                                                        fields=[self.bot.field_item(name='EXAMPLE:', value=item.get('example').replace('[', '*').replace(']', '*'), inline=False),
                                                                                self.bot.field_item(name='LINK:', value=item.get('permalink'), inline=False)],
                                                                        thumbnail="https://gamers-palace.de/wordpress/wp-content/uploads/2019/10/Urban-Dictionary-e1574592239378-820x410.jpg")
                        await ctx.send(**_embed_data)
                        await asyncio.sleep(1)

    @ auto_meta_info_command(enabled=get_command_enabled('make_figlet'))
    @ allowed_channel_and_allowed_role_2()
    @ commands.cooldown(1, 60, commands.BucketType.channel)
    async def make_figlet(self, ctx, *, text: str):
        """
        Posts an ASCII Art version of the input text.

        **Warning, your invoking message gets deleted!**

        Args:
            text (str): text you want to see as ASCII Art.

        Example:
            @AntiPetros make_figlet The text to figlet
        """
        figlet = Figlet(font='gothic', width=300)
        new_text = figlet.renderText(text.upper())

        await ctx.send(f"```fix\n{new_text}\n```")
        await ctx.message.delete()

    @staticmethod
    def paste_together(*images):
        amount = len(images)
        spacing = 25
        dice_per_line = 10
        if amount <= 10:
            b_image_size = ((images[0].size[0] * amount) + (spacing * amount), images[0].size[1])
        else:
            b_image_size = ((images[0].size[0] * dice_per_line) + (spacing * dice_per_line), (images[0].size[1] * ceil(amount / dice_per_line)) + (spacing * ceil(amount / dice_per_line)))
        b_image = Image.new('RGBA', b_image_size, color=(0, 0, 0, 0))
        current_x = 0
        current_y = 0
        for index, image in enumerate(images):
            b_image.paste(image, (current_x, current_y))
            current_x += image.size[0] + spacing
            if (index + 1) % dice_per_line == 0:
                current_x = 0
                current_y += image.size[1] + spacing

        return b_image

    async def parse_dice_line(self, dice_line: str):
        _out = []
        statements = dice_line.split()
        for statement in statements:
            statement_match = self.dice_statement_regex.search(statement)
            if statement_match:
                _out.append((int(statement_match.group('amount')), statement_match.group('dice_type')))
            else:
                raise ParseDiceLineError(statement)
        return _out

    @staticmethod
    async def _roll_the_dice(sides):
        return secrets.randbelow(sides) + 1

    @staticmethod
    def _get_dice_images(result_image_file_paths):
        images = [Image.open(dice_image) for dice_image in result_image_file_paths]
        return images

    @staticmethod
    def _sum_dice_results(in_result):
        result_dict = {key: sum(value) for key, value in in_result.items()}
        result_combined = sum(value for key, value in result_dict.items())

        return result_combined

    @auto_meta_info_command(enabled=get_command_enabled('roll_dice'))
    @allowed_channel_and_allowed_role_2(True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def roll_dice(self, ctx, *, dice_line: str):  # @AntiPetros roll_dice 14d4 14d6 14d8 14d10 14d12 14d20 14d100
        """
        Roll Dice and get the result also as Image.

        All standard DnD Dice are available, d4, d6, d8, d10, d12, d20, d100.

        Args:
            dice_line (str): the dice you want to roll in the format `2d6`, first number is amount. Multiple different dice can be rolled, just seperate them by a space `2d6 4d20 1d4`.
        """
        dice_limit = 100
        results = {}

        result_image_files = []
        parsed_dice_line = await self.parse_dice_line(dice_line)

        if sum(item[0] for item in parsed_dice_line) > dice_limit:
            await ctx.send(f"Amount of overall dice `{sum(item[1] for item in await self.parse_dice_line(dice_line))}` is over the limit of `{dice_limit}`, aborting!", delete_after=120)
            return

        for amount, type_of_dice in await self.parse_dice_line(dice_line):
            mod_type_of_dice = type_of_dice.casefold()

            if mod_type_of_dice not in self.dice_mapping:
                await ctx.reply(f"I dont know dice of the type `{type_of_dice}`!", delete_after=120)
                return

            sides_of_die = self.dice_mapping[mod_type_of_dice].get('sides')
            if mod_type_of_dice not in results:
                results[mod_type_of_dice] = []

            for i in range(amount):
                roll_result = await self._roll_the_dice(sides_of_die)
                results[mod_type_of_dice].append(roll_result)
                result_image_files.append(APPDATA[f"{mod_type_of_dice}_{roll_result}.png"])
                await asyncio.sleep(0)

        await self.bot.execute_in_thread(random.shuffle, result_image_files)
        result_images = await self.bot.execute_in_thread(self._get_dice_images, result_image_files)
        result_image = await self.bot.execute_in_thread(self.paste_together, *result_images)
        result_combined = await self.bot.execute_in_thread(self._sum_dice_results, results)
        fields = [self.bot.field_item(name="Sum", value='`' + str(result_combined) + '`', inline=False)]

        embed_data = await self.bot.make_generic_embed(title=f'{ctx.author.display_name} rolled:',
                                                       fields=fields,
                                                       thumbnail='no_thumbnail',
                                                       image=result_image,
                                                       color='random')
        await ctx.send(**embed_data)

    @auto_meta_info_command(enabled=get_command_enabled('choose_random'))
    @allowed_channel_and_allowed_role_2(in_dm_allowed=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def choose_random(self, ctx: commands.Context, select_amount: Optional[int] = 1, *, choices: str):
        """
        Selects random items from a semi-colon(`;`) seperated list. No limit on how many items the list can have, except for Discord character limit.

        Amount of item to select can be set by specifying a number before the list. Defaults to selecting only 1 item. Max amount is 25.

        Args:

            choices (str): input list as semi-colon seperated list.
            select_amount (Optional[int], optional): How many items to select. Defaults to 1.

        Example:
            `@AntiPetros 2 this is the first item; this is the second; this is the third`
        """
        if select_amount > 25:
            embed_data = await self.bot.make_generic_embed(title="Amount too high",
                                                           description="Maximum value for `selection_amount` is 25.",
                                                           thumbnail="cancelled",
                                                           footer={'text': "The Discord Embed field limit is the reason for this."},
                                                           color='colorless')
            await ctx.reply(**embed_data, delete_after=120)
            return
        async with ctx.typing():
            random.seed(None)
            await asyncio.sleep(1)
            choices = choices.strip(';')
            choice_items = [choice.strip() for choice in choices.split(';') if choice.strip() != '']
            if select_amount > len(choice_items):
                embed_data = await self.bot.make_generic_embed(title="Items to select greater than items",
                                                               description="The number of items to select from the list is greater than the amount of items in the list",
                                                               thumbnail="cancelled",
                                                               color='colorless')
                await ctx.reply(**embed_data, delete_after=120)
                return
            result = random.sample(choice_items, k=select_amount)
            fields = []
            description = ''
            if select_amount > 1:
                for result_number, result_item in enumerate(result):
                    fields.append(self.bot.field_item(name=f"No. {result_number+1}", value=f"⇒ *{result_item}*"))
            else:
                description = f'⇒ *{result[0]}*'
            embed_data = await self.bot.make_generic_embed(title=f'{ctx.invoked_with.title()} Results',
                                                           description=description,
                                                           fields=fields,
                                                           thumbnail="random")
            await ctx.reply(**embed_data)

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [Embeds]

# endregion [Embeds]

# region [HelperMethods]


# endregion [HelperMethods]

# region [SpecialMethods]


    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(KlimBimCog(bot)))
