# region [Imports]

# * Standard Library Imports -->
import os
from datetime import datetime
from collections import namedtuple
import traceback
# * Third Party Imports -->
from discord.ext import commands, tasks
import discord

from async_property import async_property
from discord import Embed, File
from watchgod import awatch
from concurrent.futures import ThreadPoolExecutor

# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.engine.special_prefix import when_mentioned_or_roles_or
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson
from antipetros_discordbot.utility.misc import sync_to_async
# endregion[Imports]


# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]

# TODO: create regions for this file
# TODO: Document and Docstrings
# IDEA: Use an assistant class to hold some of the properties and then use the __getattr__ to make it look as one object, just for structuring


class AntiPetrosBot(commands.Bot):
    executor = ThreadPoolExecutor(3, thread_name_prefix='Bot_Thread')
    admin_cog_import_path = "antipetros_discordbot.cogs.admin_cogs.admin_cog"
    embed_symbols = loadjson(APPDATA["embed_symbols.json"])
    cog_import_base_path = BASE_CONFIG.get('general_settings', 'cogs_location')

    def __init__(self, *args, ** kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = datetime.utcnow()
        self.max_message_length = 2000
        self.commands_executed = 0
        self.bot_member = None
        self.all_bot_roles = []
        if BASE_CONFIG.getboolean('startup_message', 'use_startup_message') is True:
            self.startup_message = (BASE_CONFIG.getint('startup_message', 'channel'), BASE_CONFIG.get('startup_message', 'message'))
        else:
            self.startup_message = None
        self.setup()

        glog.class_init_notification(log, self)

    def setup(self):
        self.get_initial_cogs()
        self.get_bot_roles_loop.start()

    def get_initial_cogs(self):
        self.load_extension(self.admin_cog_import_path)
        log.debug("loaded extension\cog: '%s' from '%s'", self.admin_cog_import_path.split('.')[-1], self.admin_cog_import_path)
        for _cog in BASE_CONFIG.options('extensions'):
            if BASE_CONFIG.getboolean('extensions', _cog) is True:
                name = _cog.split('.')[-1]
                full_import_path = self.cog_import_base_path + '.' + _cog
                self.load_extension(full_import_path)
                log.debug("loaded extension-cog: '%s' from '%s'", name, full_import_path)
        log.info("extensions-cogs loaded: %s", ', '.join([_ex_cog for _ex_cog in self.cogs]))

    @staticmethod
    def activity_from_config(option='standard_activity'):
        activity_dict = {'playing': discord.ActivityType.playing,
                         'watching': discord.ActivityType.watching,
                         'listening': discord.ActivityType.listening,
                         'streaming': discord.ActivityType.streaming}
        text, activity_type = BASE_CONFIG.getlist('activity', option)
        if activity_type not in activity_dict:
            log.critical("'%s' is not an Valid ActivityType, aborting activity change")
            return
        activity_type = activity_dict.get(activity_type)

        return discord.Activity(name=text, type=activity_type)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.channel.send(f'{ctx.author.mention} Sorry,Bot is busy! Please retry in a minute')
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(f'{ctx.author.mention} I have recently used this command and it is on cooldown still.')
        else:
            log.error('Ignoring exception in command {}:'.format(ctx.command))
            log.error(str(error), exc_info=True)

    @tasks.loop(minutes=30, reconnect=True)
    async def get_bot_roles_loop(self):
        log.info('Starting Refreshing Bot Roles')
        self.all_bot_roles = []
        self.bot_member = await self.retrieve_member(self.antistasi_guild.id, self.id)
        for index, role in enumerate(self.bot_member.roles):
            if index != 0:
                self.all_bot_roles.append(role)
        if BASE_CONFIG.getboolean('prefix', 'invoke_by_role_and_mention') is True:
            self.command_prefix = when_mentioned_or_roles_or(BASE_CONFIG.get('prefix', 'command_prefix'))
        else:
            self.command_prefix = BASE_CONFIG.get('prefix', 'command_prefix')
        log.info('Finished Refreshing Bot Roles')

    @get_bot_roles_loop.before_loop
    async def before_get_bot_roles_loop(self):
        await self.wait_until_ready()

    @property
    def antistasi_guild(self):
        return self.get_guild(BASE_CONFIG.getint('general_settings', 'antistasi_guild_id'))

    @property
    def id(self):
        return self.user.id

    @property
    def display_name(self):
        return self.user.display_name

    @property
    def is_debug(self):
        return BASE_CONFIG.getboolean('general_settings', 'is_debug')

    @property
    def blacklist_user(self):
        return list(map(int, BASE_CONFIG.getlist('blacklist', 'user')))

    @property
    def notify_contact_member(self):
        return BASE_CONFIG.get('blacklist', 'notify_contact_member')

    @property
    def standard_embed_color(self):
        color_string = BASE_CONFIG.get('embeds', 'standard_embed_color')
        return int(color_string, base=16)

    @property
    def std_date_time_format(self):
        return BASE_CONFIG.get('datetime', 'std_format')

    async def did_command(self):
        self.commands_executed += 1

    async def retrieve_antistasi_member(self, user_id):
        return await self.antistasi_guild.fetch_member(user_id)

    async def retrieve_member(self, guild_id, user_id):
        guild = self.get_guild(guild_id)
        return await guild.fetch_member(user_id)

    async def split_to_messages(self, ctx, message, split_on='\n'):
        _out = ''
        chunks = message.split(split_on)
        for chunk in chunks:
            if sum(map(len, _out)) < self.max_message_length:
                _out += chunk + split_on
            else:
                print(len(_out))
                await ctx.send(_out)
                _out = ''
        await ctx.send(_out)

    @sync_to_async
    def channel_from_name(self, channel_name):
        return discord.utils.get(self.antistasi_guild.channels, name=channel_name)

    @sync_to_async
    def member_by_name(self, member_name):
        member_name = member_name.casefold()
        for member in self.antistasi_guild.members:
            print(member.name)
            if member.name.casefold() == member_name:
                return member

    async def execute_in_thread(self, func, *args, **kwargs):
        return await self.loop.run_in_executor(self.executor, func, *args, **kwargs)

    async def make_basic_embed(self, title, text=None, footer=None, symbol=None, **kwargs):
        embed_title = str(title).title()
        embed_text = '' if text is None else str(text)

        basic_embed = Embed(title=embed_title, description=embed_text, color=self.standard_embed_color)
        if symbol is not None:
            basic_embed.set_thumbnail(url=self.embed_symbols.get(symbol.casefold(), None))
        for key, value in kwargs.items():
            field_name = key.replace('_', ' ').title()
            if isinstance(value, tuple):
                field_value = str(value[0])
                field_in_line = value[1]
            else:
                field_value = str(value)
                field_in_line = False
            basic_embed.add_field(name=field_name, value=field_value, inline=field_in_line)
        if footer is not None:
            if isinstance(footer, tuple):
                footer_icon_url = self.embed_symbols.get(footer[1].casefold(), None)
                basic_embed.set_footer(text=str(footer[0]), icon_url=footer_icon_url)
            else:
                basic_embed.set_footer(text=str(footer))
        return basic_embed

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.__class__.__name__
