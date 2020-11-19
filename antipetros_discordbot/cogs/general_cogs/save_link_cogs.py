import discord
from discord.ext import commands
from github import Github, GithubException
from datetime import datetime, timedelta
from gidtools.gidfiles import writejson, loadjson, pathmaker
import os
from collections import namedtuple
from pprint import pformat
from urllib.parse import urlparse
from antipetros_discordbot.data.config.config_singleton import BASE_CONFIG, COGS_CONFIG
from antipetros_discordbot.utility.locations import find_path
from antipetros_discordbot.utility.misc import config_channels_convert
from concurrent.futures import ThreadPoolExecutor
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
from asyncio import get_event_loop
import requests


class SaveLink(commands.Cog):
    channel_settings = namedtuple('ChannelSettings', ['name', 'id', 'save_file'])
    blocklist_hostfile_url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts"

    def __init__(self, bot):
        self.bot = bot
        self.number = '1'
        self.save_file = pathmaker(THIS_FILE_DIR, 'link_test.json')
        self.allowed_channels = config_channels_convert(COGS_CONFIG.getlist('save_link', 'allowed_channels'))
        self.forbidden_links = []
        self.forbidden_url_words = loadjson(find_path('forbidden_url_words.json'))
        self.create_forbidden_link_list()

    def process_raw_blocklist_content(self, raw_content):
        _out = []
        for line in raw_content.splitlines():
            if line.startswith('0') and line not in ['', '0.0.0.0 0.0.0.0']:
                line = line.split('#')[0].strip()
                _, forbidden_url = line.split(' ')
                _out.append(forbidden_url.strip())
        return set(_out)

    def create_forbidden_link_list(self):
        _loop = get_event_loop()
        _response = requests.get(self.blocklist_hostfile_url)
        _content = _response.content.decode('utf-8', errors='ignore')
        self.forbidden_links = self.process_raw_blocklist_content(_content)

    async def save_to_json(self, inputer, link_name, now_time, delete_time, link):
        if os.path.isfile(self.save_file) is True:
            _json = loadjson(self.save_file)
        else:
            _json = {}
        _json[link_name] = (inputer, now_time, delete_time, link)
        writejson(_json, self.save_file)

    @commands.command()
    @commands.has_any_role(*COGS_CONFIG.getlist('save_link', 'allowed_roles'))
    async def save_link(self, ctx, link, link_name, days_to_hold: int = None):
        if ctx.channel.name in self.allowed_channels:
            _days = 7 if days_to_hold is None else days_to_hold
            _now = datetime.now()
            _delete_time = _now + timedelta(days=_days)

            _inputer = str(ctx.author)
            link = urlparse(link, scheme='https').geturl().replace('///', '//')
            if all(forbidden_link.casefold() not in link.casefold() for forbidden_link in self.forbidden_links) and all(forbidden_word.casefold() not in link.casefold() for forbidden_word in self.forbidden_url_words):
                await self.save_to_json(_inputer, link_name, _now.isoformat(timespec='seconds'), _delete_time.isoformat(timespec='seconds'), link)
                _post = f"from: **{ctx.author.name}**\navailable until: **{_delete_time.isoformat(timespec='seconds')}**\n\nlink: **{link_name}**\n{link}"
                await ctx.send(_post, delete_after=_days * 86400)
            else:
                await ctx.send('you tried to save a link that is either in my forbidden_link list or contains a forbidden word\n\n**The link has NOT been saved!**')

    def channel_from_id(self, _id):
        return self.bot.get_channel(_id)


def setup(bot):
    bot.add_cog(SaveLink(bot))
