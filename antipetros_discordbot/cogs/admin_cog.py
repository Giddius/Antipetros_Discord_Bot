import discord
from discord import DiscordException
from discord.ext import commands
from github import Github, GithubException
from datetime import datetime, timedelta
from gidtools.gidfiles import writejson, loadjson, pathmaker
import os
from collections import namedtuple
from pprint import pformat
from antipetros_discordbot.data.config.config_singleton import BASE_CONFIG, COGS_CONFIG
from urllib.parse import urlparse
from antipetros_discordbot.utility.misc import config_channels_convert
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


class Administration(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = config_channels_convert(COGS_CONFIG.getlist('save_suggestions', 'allowed_channels'))

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def reload_all_ext(self, ctx):
        if ctx.channel.name in self.allowed_channels:
            _extensions_list = []
            _base_location = BASE_CONFIG.get('general_settings', 'cogs_location')
            for _extension in BASE_CONFIG.options('extensions'):
                if BASE_CONFIG.getboolean('extensions', _extension) is True:
                    try:
                        self.bot.reload_extension(_base_location + '.' + _extension)
                        _extensions_list.append(_extension)
                    except DiscordException as error:
                        print(str(error))
            reloaded_extensions = '\n'.join(_extensions_list)
            await ctx.send(f"**successfully reloaded the following extensions:**\n{reloaded_extensions}")

    @commands.command(name='die_antipetros_die')
    @commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    async def shutdown(self, ctx):
        if ctx.channel.name in self.allowed_channels:
            await ctx.send('cya!')
            await self.bot.logout()


def setup(bot):
    bot.add_cog(Administration(bot))
