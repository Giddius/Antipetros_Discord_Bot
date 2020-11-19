import discord
from discord.ext import commands
from github import Github, GithubException
from datetime import datetime, timedelta
from gidtools.gidfiles import writejson, loadjson, pathmaker
import os
from collections import namedtuple
from pprint import pformat
from antipetros_discordbot.data.config.config_singleton import BASE_CONFIG, COGS_CONFIG
from antipetros_discordbot.utility.locations import find_path
from antipetros_discordbot.utility.misc import config_channels_convert
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))


class SaveSuggestion(commands.Cog):
    channel_settings = namedtuple('ChannelSettings', ['name', 'id', 'save_file'])

    def __init__(self, bot):
        self.bot = bot
        self.number = '1'
        self.save_file = find_path(COGS_CONFIG.get('save_suggestions', 'save_file'))
        self.allowed_channels = config_channels_convert(COGS_CONFIG.getlist('save_suggestions', 'allowed_channels'))

    async def save_to_json(self, user, message, time):
        if os.path.isfile(self.save_file) is True:
            _json = loadjson(self.save_file)
        else:
            _json = {}
        if user not in _json:
            _json[user] = []
        _json[user].append((time, message))
        writejson(_json, self.save_file)

    @commands.Cog.listener()
    @commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def on_raw_reaction_add(self, payload):
        user = await self.bot.fetch_user(payload.user_id)
        if user.name != self.bot.user.name and user.id != 155149108183695360:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            now_time = datetime.now().isoformat(timespec='seconds')
            if any(_channel_id == payload.channel_id for _channel_name, _channel_id in self.allowed_channels.items()):
                await self.save_to_json(str(message.author), message.content, now_time)
                await channel.send(f"""{message.author.mention} I have saved this message of yours!
                                If you don't want it saved send the following message in this channel and I will delete the saved message ----> `-$-delete_my_message`!

                                If you want to see all the data I have saved from you, use `-$-request_my_data` and I will send you your data as pm!
                                If you want me to delete all your saved data, use `-$-delete_all_my_data` !warning! this is not reversible and the dev team most likely will not be able to consider the deleted suggestions""")

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def clear_all(self, ctx):
        if ctx.channel.name in self.allowed_channels:
            writejson({}, self.save_file)
            _msg = 'I have cleared the file'
        else:
            _msg = 'you dont have the permission for that'
        await ctx.send(_msg)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def retrieve_all(self, ctx):
        _txt = ''
        x = loadjson(self.save_file)
        if x != {}:
            for key, value in x.items():
                _txt += '**' + key + '**\n'
                for _time, _msg in value:
                    _txt += '- ' + _time + ' ----> ' + _msg + '\n\n'
                _txt += '-----------\n\n'
        else:
            _txt = 'no saved entries found'
        await ctx.send(_txt)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('save_suggestions', 'allowed_roles'))
    async def request_my_data(self, ctx):
        user = ctx.author
        _json = loadjson(self.save_file)
        _data = _json.get(str(user), None)
        if _data is None:
            await user.send('we have nothing saved from you')
        else:
            _out = ''
            for time, _save_content in _data:
                _out += f'**At {time} we saved this message from you:**\n```{_save_content}```\n\n'
            await user.send(_out)

    def channel_from_id(self, _id):
        return self.bot.get_channel(_id)


def setup(bot):
    bot.add_cog(SaveSuggestion(bot))
