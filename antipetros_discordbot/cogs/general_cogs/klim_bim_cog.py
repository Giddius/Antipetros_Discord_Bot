
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
import secrets
from datetime import datetime
from typing import List, Set, Dict, Tuple, Union
import asyncio
from urllib.parse import quote as urlquote
from textwrap import dedent
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands
from discord import AllowedMentions
from pyfiglet import Figlet
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
from antipetros_discordbot.utility.enums import RequestStatus, CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
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
    Soon
    """
    # region [ClassAttributes]
    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.WORKING | CogState.FEATURE_MISSING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 03:32:39",
                             "05703df4faf098a7f3f5cea49c51374b3225162318b081075eb0745cc36ddea6ff11d2f4afae1ac706191e8db881e005104ddabe5ba80687ac239ede160c3178")}

    required_config_data = dedent("""
                                        coin_image_heads = https://i.postimg.cc/XY4fhCf5/antipetros-coin-head.png,
                                        coin_image_tails = https://i.postimg.cc/HsQ0B2yH/antipetros-coin-tails.png""")

    # endregion [ClassAttributes]

    # region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        self.user_info_transform_table = {'id': lambda x: f"```py\n{x}\n```",
                                          'top_role': lambda x: f"> ♔ {x.mention} ♔",
                                          'roles': lambda x: '\n'.join(f"> ⍟ {role.mention}" for role in x),
                                          'created_at': lambda x: f"```fix\n{x.strftime(self.bot.std_date_time_format)}\n```",
                                          'joined_at': lambda x: f"```fix\n{x.strftime(self.bot.std_date_time_format)}\n```",
                                          'raw_status': lambda x: f'> {x.title()}',
                                          'public_flags': lambda x: '```diff\n' + '\n'.join(f"- {name} = {' '*(25 - len(name))}{value}" if value is False else f"+ {name} = {' '*(25 - len(name))}{value}" for name, value in x) + '\n```',
                                          'premium_since': lambda x: '> ⚡ Boosting the Discord Guild since ⚡\n' + f"```fix\n{x.strftime(self.bot.std_date_time_format)}\n```" if x is not None else '🌧️ Not boosting the Discord Guild 🌧️',
                                          'activity': lambda x: f"> {x}",
                                          'guild_permissions': lambda x: '```ini\n' + '\n'.join(f"{name} = {' '*(22-len(name))}{value}" for name, value in x if value is True) + '\n```'}

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def user_info_to_show(self):
        return COGS_CONFIG.retrieve(self.config_name, 'user_info_attributes', typus=List[str], direct_fallback=['id', 'top_role', 'roles', 'created_at', 'joined_at', 'premium_since', 'raw_status', 'activity', 'guild_permissions'])


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
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

        """
        suprise_dragon_check = secrets.randbelow(100) + 1
        if suprise_dragon_check == 1:
            await ctx.send('https://i.redd.it/073kp5pr5ev11.jpg')
        elif suprise_dragon_check == 2:
            await ctx.send('https://www.sciencenewsforstudents.org/wp-content/uploads/2019/11/860-dragon-header-iStock-494839519.gif')
        else:
            await ctx.send(THE_DRAGON)

    @ auto_meta_info_command(enabled=True, hidden=True)
    @commands.is_owner()
    async def flip_multiple(self, ctx: commands.Context, amount: int = 1):
        nato_amount = 0
        for i in range(amount):
            await ctx.send(f'__**Item number {i+1}**__')
            res = await self.flip_coin(ctx)
            if res == 'nato, you lose!':
                nato_amount += 1

        await ctx.send(f"\n__**Nato frequency was about {(nato_amount/amount)*100} %**__")

    @ auto_meta_info_command(enabled=get_command_enabled('flip_coin'))
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def flip_coin(self, ctx: commands.Context):
        """
        Simulates a coin flip and posts the result as an image of a Petros Dollar.

        """
        with ctx.typing():

            result = (secrets.randbelow(2) + 1)
            coin = "heads" if is_even(result) is True else 'tails'

            await asyncio.sleep(random.random() * random.randint(1, 2))

            coin_image = COGS_CONFIG.retrieve(self.config_name, f"coin_image_{coin}", typus=str)
            nato_check_num = secrets.randbelow(100) + 1
            if nato_check_num <= 1:
                coin = 'nato, you lose!'
                coin_image = "https://i.postimg.cc/cdL5Z0BH/nato-coin.png"
            embed = await self.bot.make_generic_embed(title=coin.title(), description=ZERO_WIDTH, image=coin_image, thumbnail='no_thumbnail')

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

        Args:
            text (str): text you want to see as ASCII Art.
        """
        figlet = Figlet(font='gothic', width=300)
        new_text = figlet.renderText(text.upper())
        await ctx.send(f"```fix\n{new_text}\n```")

    @auto_meta_info_command(enabled=get_command_enabled("show_user_info"))
    @allowed_channel_and_allowed_role_2(False)
    async def show_user_info(self, ctx, user: discord.Member = None):
        user = ctx.author if user is None else user
        embed_data = await self._user_info_to_embed(user)
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @auto_meta_info_command(enabled=get_command_enabled("make_hyperlink"))
    @allowed_channel_and_allowed_role_2(False)
    async def make_hyperlink(self, ctx: commands.Context, link: str, *, link_text: str):
        embed_data = await self.bot.make_generic_embed(title=discord.Embed.Empty, description=f"[🔗 __**{link_text}**__]({link})\n{ZERO_WIDTH}\n{ZERO_WIDTH}", timestamp=None, thumbnail=None)
        await ctx.send(**embed_data)
        await ctx.message.delete()

    @auto_meta_info_command(enabled=get_command_enabled("am_i_beautiful"), aliases=['am-I-beautiful?'])
    @allowed_channel_and_allowed_role_2(False)
    async def ask_if_beautiful(self, ctx: commands.Context):
        beholder_images = ["https://static.wikia.nocookie.net/forgottenrealms/images/2/2c/Monster_Manual_5e_-_Beholder_-_p28.jpg/revision/latest?cb=20200313153220",
                           "https://static.wikia.nocookie.net/forgottenrealms/images/6/66/Beholder_-_Scott_M._Fischer.jpg/revision/latest?cb=20200226103050",
                           "https://i.pinimg.com/originals/68/2d/69/682d69829f55202a0aa62db643b748fe.jpg",
                           "https://static.giga.de/wp-content/uploads/2016/03/shutterstock_1884419721.jpg"]
        b_image = random.choice(beholder_images)

        embed_data = await self.bot.make_generic_embed(title='That is for me to decide!', image=b_image, thumbnail=None)
        await ctx.reply(**embed_data)

    @auto_meta_info_command(enabled=get_command_enabled("roll_initiative"))
    @allowed_channel_and_allowed_role_2(False)
    async def roll_initiative(self, ctx: commands.Context, *users: discord.Member):
        initiatives = []
        for user in users:
            if user.id == 346595708180103170:
                initiatives.append((user, -20))
            else:
                initiatives.append((user, random.randint(1, 20)))
        initiatives = sorted(initiatives, key=lambda x: x[1], reverse=True)
        fields = [self.bot.field_item(name=f"{index+1}. {item[0].display_name}", value=f"🎲 {item[1]}\n⸻⸻⸻⸻⸻", inline=False) for index, item in enumerate(initiatives)]
        embed_data = await self.bot.make_generic_embed(title="Initiatives", fields=fields, thumbnail="https://www.clipartkey.com/mpngs/m/137-1379967_d20-clipart-critical-success-20-sided-dice-drawing.png")
        await ctx.send(**embed_data)

    @auto_meta_info_command(enabled=get_command_enabled("longest_user"))
    @allowed_channel_and_allowed_role_2(False)
    async def longest_user(self, ctx: commands.Context, typus: str = 'community'):
        async with ctx.typing():
            attr = 'created_at' if typus.casefold() == 'discord' else 'joined_at'
            longest_user = (None, datetime.utcnow())
            async for user in self.bot.antistasi_guild.fetch_members(limit=None):
                date = getattr(user, attr)
                if date < longest_user[1]:
                    longest_user = (user, date)

        await ctx.send(f"The longest user is {longest_user[0].mention} ({longest_user[0].display_name}) he {attr.replace('_',' ')} `{longest_user[1].strftime(self.bot.std_date_time_format)}`", allowed_mentions=discord.AllowedMentions.none())


# endregion [Commands]

# region [DataStorage]


# endregion [DataStorage]

# region [Embeds]


# endregion [Embeds]

# region [HelperMethods]


    async def _user_info_to_embed(self, user: discord.Member):
        # seperator = '⸻⸻⸻⸻⸻'
        master_sort_table = {"id": 0, 'top_role': 4, 'roles': 5, 'premium_since': 3, 'created_at': 1, 'joined_at': 2, 'raw_status': 6, 'activity': 7, "guild_permissions": 8}
        seperator = ''
        fields = []
        for attr in sorted(self.user_info_to_show, key=master_sort_table.get):
            name = '__**' + attr.replace('_', ' ').title() + f'**__'
            value = self.user_info_transform_table.get(attr)(getattr(user, attr))
            if attr in ["joined_at", 'activity', 'top_role', "created_at", 'activity', "raw_status"]:
                in_line = True
            else:
                in_line = False
            if attr in ["created_at", "joined_at", "guild_permissions", 'premium_since', 'raw_status', 'activity']:
                sep = ''
            else:
                sep = seperator
            fields.append(self.bot.field_item(name=name, value=f"{value}\n{sep}", inline=in_line))
        fields.append(self.bot.field_item(name='On Mobile?', value='📱' if user.is_on_mobile() is True else '💻'))
        return await self.bot.make_generic_embed(title=ZERO_WIDTH,
                                                 thumbnail=user.avatar_url,
                                                 author={"name": user.display_name, 'icon_url': user.avatar_url},
                                                 fields=fields,
                                                 footer={'text': 'You want the bot to fetch more or other data? Contact Giddi!'})

# endregion [HelperMethods]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))

# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(KlimBimCog(bot)))
