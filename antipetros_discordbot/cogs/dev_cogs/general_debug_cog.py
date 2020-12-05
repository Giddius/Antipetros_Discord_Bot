

# region [Imports]

# * Standard Library Imports -->
import os
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import asyncio
from pprint import pprint, pformat
# * Third Party Imports -->
import aiohttp
import discord
from discord.ext import tasks, commands
import discord
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.enums import RequestStatus
from antipetros_discordbot.utility.named_tuples import LINK_DATA_ITEM
from antipetros_discordbot.utility.sqldata_storager import LinkDataStorageSQLite
from antipetros_discordbot.utility.gidtools_functions import writeit, loadjson, pathmaker, writejson
from antipetros_discordbot.data.config.config_singleton import BASE_CONFIG, COGS_CONFIG

# endregion [Imports]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


# endregion [Constants]

# region [TODO]

# TODO: create regions for this file
# TODO: Document and Docstrings


# endregion [TODO]


class GeneralDebug(commands.Cog):

    config_name = 'general_debug'

    def __init__(self, bot):
        self.bot = bot
        glog.class_init_notification(log, self)

    @property
    def allowed_channels(self):
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

    @property
    def restrict_listen_to_allowedchannels(self):
        return COGS_CONFIG.getboolean(self.config_name, 'restrict_all_message_listener_to_allowedchannels')

    @property
    def enable_all_message_listener(self):
        return COGS_CONFIG.getboolean(self.config_name, 'enable_all_message_listener')

    @commands.Cog.listener(name='on_ready')
    async def _extra_cog_setup(self):
        """
        Setup methods that run if the Bot Connects successfully.

        Currently it:
            - creates a fresh forbidden_link_list json
            - retrieves the channel to save the links to from the config

        ! DOES NOT EXECUTE WHEN COG IS RELOADED !
        """

        log.info(f"{self} Cog ----> finished extra setup")

    @commands.Cog.listener(name='on_message')
    async def all_message_infos(self, ctx):
        if self.enable_all_message_listener is False or (self.restrict_listen_to_allowedchannels and ctx.channel.name not in self.allowed_channels):
            return
        to_log = [('guild_name', ctx.guild.name),
                  ('guild_id', ctx.guild.id),
                  ('channel_name', ctx.channel.name),
                  ('channel_id', ctx.channel.id),
                  ('author_name', ctx.author.name),
                  ('author_id', ctx.author.id),
                  ('message_content', ctx.content),
                  ('message_clean_content', ctx.clean_content),
                  ('created_at', ctx.created_at),
                  ('jump_url', ctx.jump_url)]
        _out = ''
        for name, result in to_log:
            _out += f"{name}: {str(result)}, "
        log.debug(_out)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('general_debug', 'allowed_roles'))
    async def last_message(self, ctx, channel_name):
        if ctx.channel.name not in self.allowed_channels:
            return
        try:
            channel = await self.bot.channel_from_name(channel_name)
            last_message_id = channel.last_message_id
            msg = await self.bot.bot_member.fetch_message(last_message_id)

            await ctx.send(f"**Message Content:**\n\n```\n{msg.content}\n```")
        except Exception as error:
            await ctx.send(f"**__Encountered this Exception:__**\n\n```python\n{str(error)}\n```")
            raise

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('general_debug', 'allowed_roles'))
    async def message_by_id(self, ctx, channel_name, msg_id: int):
        if ctx.channel.name not in self.allowed_channels:
            return
        try:
            channel = await self.bot.channel_from_name(channel_name)
            msg = await channel.fetch_message(msg_id)
            await ctx.send(f"**Message Content:**\n\n```\n{msg.content}\n```")
        except Exception as error:
            await ctx.send(f"**__Encountered this Exception:__**\n\n```python\n{str(error)}\n```")
            raise

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('general_debug', 'allowed_roles'))
    async def all_info_from_command_trigger(self, ctx, *arguments):
        if ctx.channel.name not in self.allowed_channels:
            return
        invoke_member = await self.bot.retrieve_antistasi_member(ctx.author.id)
        invoke_member_activity = invoke_member.activity

        invoke_member_activity = 'No activity' if invoke_member_activity is None else invoke_member_activity.name
        if invoke_member_activity.casefold() == 'spotify':
            invoke_member_activity = f"{invoke_member.activity.title} by {invoke_member.activity.artist} with a duration of {str(invoke_member.activity.duration)}"
        info = [('prefix', ctx.prefix),
                ('command', ctx.command),
                ('command_failed', ctx.command_failed),
                ('from cog', ctx.cog),
                ('guild', ctx.guild.name),
                ('channel', ctx.channel.name),
                ('args', ctx.args),
                ('kwargs', ctx.kwargs),
                ('message_content', ctx.message.content),
                ('caller_name', ctx.author.name),
                ('caller_roles', list(map(lambda x: x.name, invoke_member.roles))),
                ('caller_top_role', invoke_member.top_role.name),
                ('caller_activity', invoke_member_activity),
                ('created_at', ctx.message.created_at.isoformat())]

        embed = discord.Embed(title="Command Call Info")
        for _name, _value in info:
            embed.add_field(name=f"__{_name.title()}:__", value=f"`{str(_value)}`", inline=False)
        await ctx.send(embed=embed)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(GeneralDebug(bot))