

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import random
from time import time
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
import asyncio
from io import BytesIO
from textwrap import dedent
from typing import Optional
# * Third Party Imports --------------------------------------------------------------------------------->
import discord
from discord.ext.commands import Greedy
from discord.ext import commands
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from emoji import demojize
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.misc import save_commands, color_hex_embed, async_seconds_to_pretty_normal, make_config_name
from antipetros_discordbot.utility.checks import log_invoker, allowed_channel_and_allowed_role_2, command_enabled_checker, allowed_requester
from antipetros_discordbot.utility.named_tuples import MovieQuoteItem
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
from antipetros_discordbot.utility.emoji_handling import create_emoji_custom_name
# endregion [Imports]

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

COG_NAME = "GeneralDebugCog"
CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion [Constants]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]


class GeneralDebugCog(commands.Cog, command_attrs={'hidden': True, "name": COG_NAME}):
    """
    Cog for debug or test commands, should not be enabled fo normal Bot operations.
    """
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.WORKING | CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 05:26:32",
                             "a296317ad6ce67b66c11e18769b28ef24060e5dac5a0b61a9b00653ffbbd9f4e521b2481189f075d029a4e9745892052413d2364e0666a97d9ffc7561a022b07")}
    required_config_data = dedent("""
                                  """)

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support

        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')

        glog.class_init_notification(log, self)

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def emoji_tester(self, payload):
        disable = True

        if disable is True:
            return
        emoji = payload.emoji

        if emoji.is_custom_emoji():
            log.debug("custom emoji as str(): '%s'", str(emoji))
            log.debug("custom emoji id: '%s'", emoji.id)
            log.debug("custom emoji name: '%s'", emoji.name)
            log.debug("custom emoji demojized: '%s'", demojize(str(emoji)))
            log.debug("custom emoji hash: '%s'", hash(emoji))
        elif emoji.is_unicode_emoji():
            log.debug("unicode emoji as str(): '%s'", str(emoji))
            log.debug("unicode emoji id: '%s'", emoji.id)
            log.debug("unicode emoji name: '%s'", emoji.name)
            log.debug("unicode emoji demojized: '%s'", demojize(emoji.name))
            log.debug("unicode emoji hash: '%s'", hash(emoji))
            log.debug("unicode emoji customized name: '%s'", create_emoji_custom_name(str(emoji)))

    @auto_meta_info_command(enabled=get_command_enabled('roll'))
    @allowed_channel_and_allowed_role_2()
    @log_invoker(log, 'debug')
    async def roll_blocking(self, ctx, target_time: int = 1):
        start_time = time()
        time_multiplier = 151267
        random_stats_funcs = [("mean", mean),
                              ("median", median),
                              ("stdev", stdev),
                              ("variance", variance),
                              ("mode", mode),
                              ("harmonic_mean", harmonic_mean),
                              ("median_grouped", median_grouped),
                              ("pvariance", pvariance),
                              ('amount', len),
                              ('sum', sum)]
        roll_data = [random.randint(1, 10) for _ in range(target_time * time_multiplier)]

        stats_data = {}
        log.debug("starting calculating statistics")
        for key, func in random_stats_funcs:
            stats_data[key] = round(func(roll_data), ndigits=2)
            log.debug('finished calculating "%s"', key)
        time_taken_seconds = int(round(time() - start_time))
        time_taken = await async_seconds_to_pretty_normal(time_taken_seconds) if time_taken_seconds != 0 else "less than 1 second"
        await ctx.send(embed=await make_basic_embed(title='Roll Result', text='this is a long blocking command for debug purposes', symbol='debug_2', duration=time_taken, ** stats_data))

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role_2()
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def request_server_restart(self, ctx):

        if ctx.prefix != "<@&800769712879042612> ":

            return

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

    @auto_meta_info_command()
    @commands.is_owner()
    async def save_embed(self, ctx, message: discord.Message):
        if len(message.embeds) == 0:
            await ctx.send("the message has no embed, aborting")
            return

        embed = message.embeds[0]
        embed_dict = embed.to_dict()
        writejson(embed_dict, pathmaker(APPDATA["saved_embeds"], f"{message.id}.json"))
        await ctx.send(f'saved embed from message {message.id}')

    @auto_meta_info_command()
    @commands.is_owner()
    async def quick_latency(self, ctx):
        await ctx.send(f"{round(self.bot.latency * 1000)} ms")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    @auto_meta_info_command(aliases=['pin'])
    @commands.is_owner()
    async def pin_message(self, ctx: commands.Context, *, reason: str):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            return
        if ctx.message.reference.resolved is None:
            await ctx.send('you need to reply to a message, that should be pinned, aborting!')
            return
        message = ctx.message.reference.resolved
        log.debug(f"{reason=}")
        await message.pin(reason=reason)
        await ctx.message.delete()

    @auto_meta_info_command(aliases=['unpin'])
    @commands.is_owner()
    async def unpin_message(self, ctx: commands.Context, *, reason: str):
        if ctx.channel.name.casefold() not in ['bot-testing', 'bot-development']:
            return
        if ctx.message.reference.resolved is None:
            await ctx.send('you need to reply to a message, that should be pinned, aborting!')
            return
        message = ctx.message.reference.resolved
        log.debug(f"{reason=}")
        await message.unpin(reason=reason)
        await ctx.send(f'UNpinned message {message.id}', delete_after=60)
        await ctx.message.delete()

    async def _apply_overwrites(self, channel: discord.TextChannel, permissions: dict, selector):
        for name, value in list(channel.overwrites_for(selector)):
            if value is not None:
                permissions[name] = value
        return permissions

    @auto_meta_info_command(aliases=['channel_permissions'])
    @commands.is_owner()
    async def check_bot_channel_permissions(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, display_mode: Optional[str] = 'only_true'):
        channel = ctx.channel if channel is None else channel
        bot_member = self.bot.bot_member
        permissions = {}
        for name, value in channel.permissions_for(bot_member):
            permissions[name] = value
        for selector in [self.bot.bot_member] + self.bot.all_bot_roles:
            permissions = await self._apply_overwrites(channel=channel, permissions=permissions, selector=selector)
        if display_mode.casefold() == 'only_true':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is True) + '\n```'
        elif display_mode.casefold() == 'all':
            permission_list = [f"{'+' if permission_bool is True else '-'} {permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items()]
            description = '```diff\n' + '\n'.join(sorted(permission_list, key=lambda x: x.endswith('True'), reverse=True)) + '\n```'
        elif display_mode.casefold() == 'only_false':
            description = '```ini\n' + f'\n{"-"*35}\n'.join(f"{permission_name} = {' '*(25-len(permission_name))} {permission_bool}" for permission_name, permission_bool in permissions.items() if permission_bool is False) + '\n```'

        embed_data = await self.bot.make_generic_embed(title=f'Permissions for **__{self.bot.display_name.upper()}__** in **__{channel.name.upper()}__**', description=description, thumbnail=None, footer='not_set')
        await ctx.reply(**embed_data, allowed_mentions=discord.AllowedMentions.none())

    @ commands.command(aliases=get_aliases("delete_msg"))
    @ commands.is_owner()
    async def delete_msg(self, ctx, msg_id: int):

        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    @ commands.command()
    @ commands.is_owner()
    async def check_embed_gif(self, ctx: commands.Context):
        embed_data = await self.bot.make_generic_embed(title="check embed gif", image=APPDATA['COMMAND_the_dragon.gif'])
        await ctx.send(**embed_data)


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(GeneralDebugCog(bot)))
