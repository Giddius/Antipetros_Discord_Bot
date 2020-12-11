# * Standard Library Imports -->
import os
import random
import statistics
from io import BytesIO
from time import time

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import asyncio
# * Third Party Imports -->
import discord
from PIL import Image
from discord.ext import commands
import gidlogger as glog
# * Local Imports -->

from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.discord_markdown_helper.general_markdown_helper import Bold, Cursive, CodeBlock, LineCode, UnderScore, BlockQuote
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]


APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')

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
    config_name = "test_playground"

    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = set(COGS_CONFIG.getlist('test_playground', 'allowed_channels'))
        self.base_map_image = Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v3_2000_w_outposts.png")
        self.outpost_overlay = {'city': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_city_marker.png"),
                                'volcano': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_volcano_marker.png"),
                                'airport': Image.open(r"D:\Dropbox\hobby\Modding\Ressources\Arma_Ressources\maps\tanoa_v2_2000_airport_marker.png")}
        self.old_map_message = None
        self.old_messages = {}
        self.last_timeStamp = datetime.utcfromtimestamp(0)
        self.carthage_list = ["https://1.bp.blogspot.com/-OXLXIP3dgE0/XUiSIA61h-I/AAAAAAAACd4/NVCH6YmxhnkXaZ-CS3ssq4wH-ON-Hn6-gCLcBGAs/s1600/1543710269_2777777_0.jpg",
                              "https://pics.conservativememes.com/salt-the-earthsonot-hing-would-ever-grow-again-a-2-38061179.png",
                              "https://i.redd.it/h3bi3p5jurwz.jpg",
                              "https://pbs.twimg.com/media/DSrDQVFVAAAODM1.jpg",
                              "https://memegenerator.net/img/instances/58080047/carthago-delenda-est.jpg"]
        if self.bot.is_debug:
            self.save_commands()
            log.debug("commands for %s saved to commands.json")
    # @property
    # def last_map_msg(self):
    #     msg_id = COGS_CONFIG.get(self.config_name, 'last_map_image_msg_id')
    #     if msg_id == '':
    #         return None
    #     try:
    #         msg_id = int(msg_id)
    #     except ValueError:
    #         COGS_CONFIG.set(self.config_name, 'last_map_image_msg_id')
    #         return None
    #     msg = self.bot.

    def save_commands(self):
        command_json_file = r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antipetros_Discord_Bot_new\docs\commands.json"
        command_json = loadjson(command_json_file)
        command_json[str(self)] = {'file_path': pathmaker(os.path.abspath(__file__)),
                                   'description': __doc__,
                                   'commands': {(com.name + ' ' + com.signature).replace('<ctx>', '').replace('  ', ' ').strip(): com.help for com in self.get_commands()}}
        writejson(command_json, command_json_file, indent=4)
        log.debug("commands for %s saved to %s", self, command_json_file)

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
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def roll(self, ctx, sides: int = 6, amount: int = 1):
        log.info(ctx.message.raw_role_mentions)
        _result = 0
        _dice = []
        time_start = time()
        for i in range(amount):
            _rolled = random.randint(1, sides)
            _result += _rolled
            _dice.append(_rolled)
            if i + 1 % 1000000 == 0:
                await ctx.send(f'reached {str("1.000.000")} dice again', delete_after=120)

        if amount > 1:
            _stdev = statistics.stdev(_dice)
            _mean = statistics.mean(_dice)
            _median = statistics.median(_dice)
            x = statistics.mode(_dice)
            y = statistics.variance(_dice)
            out_message = f"{ctx.author.mention} **you have rolled a total of:** {str(_result)}\n**dice result:** {', '.join(map(str,_dice))}\n\n**standard deviantion:** {str(_stdev)}\n**mean:** {str(_mean)}\n**median:** {str(_median)}\n**mode:** {str(x)}\n**variance:** {str(y)}"
            if len(out_message) >= 1900:
                out_message = f"{ctx.author.mention} **you have rolled a total of:** {str(_result)}\n\n**standard deviantion:** {str(_stdev)}\n**mean:** {str(_mean)}\n**median:** {str(_median)}\n**mode:** {str(x)}\n**variance:** {str(y)}"
            await ctx.send(out_message + f'\n\n**THIS TOOK** {str(round(time()-time_start,3))} SECONDS')
        else:
            await ctx.send(f"{ctx.author.mention} you have rolled {_result}")
        await self.bot.did_command()

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

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def map_changed(self, ctx, marker, color):
        if ctx.channel.name in self.allowed_channels:

            with BytesIO() as image_binary:

                self.base_map_image, image_binary = await self.bot.execute_in_thread(self.map_image_handling, self.base_map_image, marker, color, image_binary)

                if self.old_map_message is not None:
                    await self.old_map_message.delete()
                delete_time = 30 if self.bot.is_debug is True else None
                self.old_map_message = await ctx.send(file=discord.File(fp=image_binary, filename="map.png"), delete_after=delete_time)
            self.bot.commands_executed += 1
            log.debug("finished 'map_changed' command")

    # @commands.command(name='FAQ_you')
    # async def get_faq_by_number(self, ctx, faq_number: int):

    #     if ctx.channel.name in self.allowed_channels:
    #         _faq_dict = FAQ_BY_NUMBERS
    #         _msg = _faq_dict.get(faq_number, None)

    #         if _msg is None:
    #             _msg = "Canot find the requested FAQ"
    #         else:
    #             _msg = "**FAQ you too**\n\n" + _msg
    #         await ctx.send(_msg)

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

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def check_md_helper(self, ctx, *, text):
        if ctx.channel.name not in self.allowed_channels:
            return

        _out = []
        _out.append(f'bold: {Bold(text)}')
        _out.append(f'cursive: {Cursive(text)}')
        _out.append(f'underscore: {UnderScore(text)}')
        _out.append(f'linecode: {LineCode(text)}')
        _out.append(f'codeblock no language: {CodeBlock(text)}')
        _out.append(f'codeblock python: {CodeBlock(text, "python")}')
        _out.append(f'bold_cursive: {Cursive(Bold(text))}')
        _out.append(f'bold_underscore: {UnderScore(Bold(text))}')
        _out.append(f'underscore_cursive: {Cursive(UnderScore(text))}')
        _out.append(f'bold_cursive_underscore: {UnderScore(Cursive(Bold(text)))}')
        _out.append(f'blockquote: \n{BlockQuote(text)}')
        await ctx.send('\n\n------------------------\n\n'.join(_out))

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def check_md_helper_specific(self, ctx, typus, *, text):
        if ctx.channel.name not in self.allowed_channels:
            return
        typus = typus.casefold()
        if typus == 'bold':
            await ctx.send(f'bold: {Bold(text)}')
        elif typus == 'cursive':
            await ctx.send(f'cursive: {Cursive(text)}')
        elif typus == 'underscore':
            await ctx.send(f'underscore: {UnderScore(text)}')
        elif typus == 'linecode':
            await ctx.send(f'linecode: {LineCode(text)}')
        elif typus == 'codeblock':
            if text.split(' ', 1)[0].casefold() in ['python', 'sql', 'xml', 'json', 'csv', 'bash', 'batch']:
                _language, _text = text.split(' ', 1)
                codeblock = CodeBlock(_text, _language)
            else:
                _language = 'no_language'
                codeblock = CodeBlock(text)
            await ctx.send(f'codeblock {_language}: {codeblock}')
        elif typus in ['cursive_bold', 'bold_cursive']:
            await ctx.send(f'bold_cursive: {Cursive(Bold(text))}')
        elif typus in ['underscore_bold', 'bold_underscore']:
            await ctx.send(f'bold_underscore: {UnderScore(Bold(text))}')
        elif typus in ['cursive_underscore', 'underscore_cursive']:
            await ctx.send(f'underscore_cursive: {Cursive(UnderScore(text))}')
        elif typus == 'blockquote':
            await ctx.send(f'blockquote: \n{BlockQuote(text)}')

        elif typus == 'full':
            await ctx.send(f'bold_cursive_underscore: {UnderScore(Cursive(Bold(text)))}')

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def furthermore_do_you_want_to_say_something(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        await ctx.send(random.choice(self.carthage_list))

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def big_message(self, ctx, amount: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        content = []
        for _ in range(amount // 2):
            content.append(random.randint(0, 9))
        content = map(str, content)
        content = ' '.join(content)
        print(content)
        await self.bot.split_to_messages(ctx, content, ' ')

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    async def request_server_restart(self, ctx):
        if ctx.channel.name not in self.allowed_channels:
            return
        if ctx.prefix != "<@&752957930902651062> ":
            return
        roles = await self.bot.antistasi_guild.fetch_roles()
        for role in roles:
            if role.name.casefold() == 'Dev Helper'.casefold():
                for _member in role.members:
                    print(_member.name)
        servers = ["COMMUNITY_SERVER_1", "TEST_SERVER_1", "TEST_SERVER_2"]
        await ctx.send(f"please specify the server name in the next 20 seconds | OPTIONS: {', '.join(servers)}")
        user = ctx.author
        channel = ctx.channel

        def check(m):
            return m.author.name == user.name and m.channel.name == channel.name
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=20.0)
            if any(server.casefold() in msg.content.casefold() for server in servers):
                for server in servers:
                    if server.casefold() in msg.content.casefold():
                        _server = server
            else:
                await ctx.send('No valid answer received, aborting request, you can always try again')
                return
            await ctx.send("Did the commander save and is everyone ready for a restart? answer time: 20 seconds | OPTIONS: YES, NO")
            try:
                msg_2 = await self.bot.wait_for('message', check=check, timeout=20.0)
                if msg_2.content.casefold() == 'yes':
                    is_saved = 'yes'
                elif msg_2.content.casefold() == 'no':
                    is_saved = 'no'
                else:
                    await ctx.send('No valid answer received, aborting request, you can always try again')
                    return
                await ctx.send("notifying admin now")
                member = await self.bot.retrieve_antistasi_member(576522029470056450)
                await member.send(f"This is a notification from {ctx.author.name}!\nHe requests a server restart for server {_server}, saved and ready: {is_saved}")
                await ctx.send(f"I have notified {member.name} per DM!")
            except asyncio.TimeoutError:
                await ctx.send('No answer received, aborting request, you can always try again')
                return

        except asyncio.TimeoutError:
            await ctx.send('No answer received, aborting request, you can always try again')
            return

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__

# endregion [SpecialMethods]


def setup(bot):
    bot.add_cog(TestPlayground(bot))
