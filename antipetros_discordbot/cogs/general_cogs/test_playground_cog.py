import discord
from discord.ext import commands
from github import Github, GithubException
from datetime import datetime, timedelta
from gidtools.gidfiles import writejson, loadjson, pathmaker
import os
import random
from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple
from pprint import pformat
from io import BytesIO
from antipetros_discordbot.data.config.config_singleton import BASE_CONFIG, COGS_CONFIG
from antipetros_discordbot.utility.locations import find_path
from antipetros_discordbot.utility.misc import config_channels_convert
from antipetros_discordbot.data.fixed_data.faq_data import FAQ_BY_NUMBERS
from PIL import Image, ImageFont, ImageDraw
from tempfile import TemporaryDirectory


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


FAQ_THING = """**FAQ No 17**
_How to become a server member?_
_Read the channel description on teamspeak or below_

_**Becoming a member:**_
```
Joining our ranks is simple: play with us and participate in this community! If the members like you you may be granted trial membership by an admin upon recommendation.

Your contribution and participation to this community will determine how long the trial period will be, and whether or not it results in full membership. As a trial member, you will receive in-game membership and a [trial] tag on these forums which assures you an invite to all events including official member meetings. Do note that only full members are entitled to vote on issues at meetings.
```"""


class TestPlayground(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = config_channels_convert(COGS_CONFIG.getlist('test_playground', 'allowed_channels'))
        self.base_map_image = Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v3_2000_w_outposts.png")
        self.outpost_overlay = {'city': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_city_marker.png"),
                                'volcano': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_volcano_marker.png"),
                                'airport': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_airport_marker.png")}
        self.old_map_message = None
        self.old_messages = {}
        self.last_timeStamp = datetime.utcfromtimestamp(0)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def embed_experiment(self, ctx):
        if ctx.channel.name in self.allowed_channels:
            embed = discord.Embed(title='this is a test embed'.title(), description=f'it is posted in {ctx.channel.name}')
            embed.add_field(name='From', value=ctx.author.name)
            embed.set_footer(text='destroy all humans'.upper())
            await ctx.send(embed=embed)

    @commands.command(name='changesettings')
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def change_setting_to(self, ctx, config, section, option, value):

        if ctx.channel.name in self.allowed_channels:
            if config.casefold() in ['base_config', 'cogs_config']:
                if config.casefold() == 'base_config':
                    _config = BASE_CONFIG
                elif config.casefold() == 'cogs_config':
                    _config = COGS_CONFIG

                if section in _config.sections():
                    _config.set(section, option, value)
                    _config.save()
                    await ctx.send(f"change the setting '{option}' in section '{section}' to '{value}'")
                else:
                    await ctx.send('no such section in the specified config')
            else:
                await ctx.send('config you specified does not exist!')

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def roll_a_d(self, ctx, sides: int, amount: int = 1):
        _result = 0
        _dice = []
        for _ in range(amount):
            _rolled = random.randint(1, sides)
            _result += _rolled
            _dice.append(_rolled)
        await ctx.send(f"**you have rolled a total of:** {str(_result)}\n**dice result:** {', '.join(map(str,_dice))}")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def map_changed(self, ctx, marker, color):
        if ctx.channel.name in self.allowed_channels:
            marker_image = self.outpost_overlay.get(marker)
            marker_alpha = marker_image.getchannel('A')
            marker_image = Image.new('RGBA', marker_image.size, color=color)
            marker_image.putalpha(marker_alpha)
            self.base_map_image.paste(marker_image, mask=marker_alpha)

            with BytesIO() as image_binary:
                self.base_map_image.save(image_binary, 'PNG', optimize=True)
                image_binary.seek(0)
                if self.old_map_message is not None:
                    await self.old_map_message.delete()
                self.old_map_message = await ctx.send(file=discord.File(fp=image_binary, filename="map.png"))

    @commands.command(name='FAQ_you')
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def get_faq_by_number(self, ctx, faq_number: int):
        if ctx.channel.name in self.allowed_channels:
            print('is correct channel')
            _faq_dict = FAQ_BY_NUMBERS
            _msg = _faq_dict.get(faq_number, None)

            if _msg is None:
                print("_msg is none")
                _msg = "Canot find the requested FAQ"
            else:
                _msg = "**FAQ you too**\n\n" + _msg
            await ctx.send(_msg)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     _channel = message.channel
    #     if _channel.name == "bot-development-and-testing" and message.author.name != self.bot.user.name:
    #         time_difference = (datetime.utcnow() - self.last_timeStamp).total_seconds()
    #         if time_difference > 500:
    #             _old_message = self.old_messages.get(_channel.name, None)
    #             if _old_message is not None:
    #                 try:
    #                     await _old_message.delete()
    #                 except discord.errors.NotFound:
    #                     print("old_message_was deleted")
    #             self.old_messages[_channel.name] = await _channel.send(f"**this message will always be the last message in the channel**")
    #             self.last_timeStamp = datetime.utcnow()


def setup(bot):
    bot.add_cog(TestPlayground(bot))
