

# region [Imports]

# * Standard Library Imports -->

import asyncio
import gc
import logging
import os
import re
import sys
import json
import lzma
import time
import queue
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from statistics import mean, median, stdev, mode, variance, pvariance
import random
from io import BytesIO
# * Third Party Imports -->

from discord.ext import commands, tasks
from discord import DiscordException
import discord
from fuzzywuzzy import process as fuzzprocess
import matplotlib.pyplot as plt
# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.misc import seconds_to_pretty, handle_arguments_string
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, pickleit, get_pickled
from antipetros_discordbot.utility.data_gathering import gather_data
from antipetros_discordbot.utility.embed_helpers import make_basic_embed
from antipetros_discordbot.utility.misc import save_commands, seconds_to_pretty, async_seconds_to_pretty_normal
from antipetros_discordbot.utility.checks import in_allowed_channels, PURGE_CHECK_TABLE, purge_check_always_false, purge_check_always_true
from antipetros_discordbot.utility.named_tuples import FeatureSuggestionItem
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class AdministrationCog(commands.Cog, command_attrs={'hidden': True, "name": "AdministrationCog"}):
    # region [ClassAttributes]

    config_name = 'admin'
    shutdown_message_pickle_file = pathmaker(APPDATA['temp_files'], 'last_shutdown_message.pkl')
    # endregion[ClassAttributes]

# region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.all_configs = [BASE_CONFIG, COGS_CONFIG]
        self.config_dir = APPDATA['config']
        self.do_not_reload_cogs = ['admin_cog', 'performance_cog']
        if self.bot.is_debug:
            save_commands(self)
        glog.class_init_notification(log, self)


# endregion[Init]

# region [Properties]

    @ property
    def allowed_dm_invoker_ids(self):
        return set(map(int, COGS_CONFIG.getlist(self.config_name, 'allowed_dm_ids')))

    @ property
    def allowed_channels(self):
        return set(COGS_CONFIG.getlist(self.config_name, 'allowed_channels'))

# endregion[Properties]

    async def on_ready_setup(self):
        if os.path.isfile(self.shutdown_message_pickle_file):
            last_shutdown_message = get_pickled(self.shutdown_message_pickle_file)
            channel_id = last_shutdown_message.get('channel_id')
            message_id = last_shutdown_message.get('message_id')
            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
            os.remove(self.shutdown_message_pickle_file)

    async def _get_available_configs(self):  # sourcery skip: dict-comprehension
        found_configs = {}
        for _file in os.scandir(self.config_dir):
            if 'config' in _file.name and os.path.splitext(_file.name)[1] in ['.ini', '.json', '.yaml', '.toml']:
                found_configs[os.path.splitext(_file.name)[0]] = _file.name
        return found_configs

    async def _config_file_to_discord_file(self, config_name):
        config_path = pathmaker(self.config_dir, config_name) if '/' not in config_name else config_name
        return discord.File(config_path, config_name)

    async def _match_config_name(self, config_name_input):
        available_configs = await self._get_available_configs()
        _result = fuzzprocess.extractOne(config_name_input, choices=available_configs.keys(), score_cutoff=80)
        if _result is None:
            return None
        else:
            return pathmaker(self.config_dir, available_configs[_result[0]])

    @ commands.command(aliases=get_aliases("make_feature_suggestion"))
    async def make_feature_suggestion(self, ctx, *, message):

        author = ctx.author
        extra_data = (ctx.message.attachments[0].filename, await ctx.message.attachments[0].read()) if len(ctx.message.attachments) != 0 else None

        author_roles = [role.name for role in author.roles if 'everyone' not in role.name.casefold()]

        now = datetime.utcnow()

        extra_data_path = None
        if extra_data is not None:

            extra_data_path = await self.bot.save_feature_suggestion_extra_data(*extra_data)
        fmt = self.bot.std_date_time_format
        mod_message = message if len(message) < 1024 else 'see next message'
        feature_suggestion_item = FeatureSuggestionItem(author.name, author.nick, author.id, author_roles, author.top_role.name, author.joined_at.strftime(fmt), now.strftime(fmt), mod_message, extra_data_path)
        embed = await make_basic_embed(title='New Feature Suggestion', text=f'send from channel `{ctx.channel.name}`', symbol='save', **feature_suggestion_item._asdict())
        await self.bot.message_creator(embed=embed)
        if mod_message == 'see next message':
            await self.bot.message_creator(message=message)
        feature_suggestion_item = feature_suggestion_item._replace(message=message)
        await self.bot.add_to_feature_suggestions(feature_suggestion_item)
        await ctx.send(content=f"your suggestion has been sent to the bot creator --> **{self.bot.creator.name}** <--")

    @ commands.command(aliases=get_aliases("reload_all_ext"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def reload_all_ext(self, ctx):
        standard_space_amount = 30
        BASE_CONFIG.read()
        COGS_CONFIG.read()
        reloaded_extensions = {}
        _base_location = BASE_CONFIG.get('general_settings', 'cogs_location')
        for _extension in BASE_CONFIG.options('extensions'):
            if _extension not in self.do_not_reload_cogs and BASE_CONFIG.getboolean('extensions', _extension) is True:
                _location = _base_location + '.' + _extension
                try:
                    self.bot.unload_extension(_location)
                    self.bot.load_extension(_location)
                    log.debug('Extension Cog "%s" was successfully reloaded from "%s"', _extension.split('.')[-1], _location)
                    _category, _extension = _extension.split('.')

                    if _category not in reloaded_extensions:
                        reloaded_extensions[_category] = ""
                    spaces = ' ' * (standard_space_amount - len(_extension))
                    reloaded_extensions[_category] += f"*{_extension}:*\n:white_check_mark:\n\n"
                except DiscordException as error:
                    log.error(error)

        _delete_time = 15 if self.bot.is_debug is True else 60
        await ctx.send(embed=await make_basic_embed(title="**successfully reloaded the following extensions**", symbol="update", **reloaded_extensions), delete_after=_delete_time)
        await ctx.message.delete(delay=float(_delete_time))

    @ commands.command(aliases=get_aliases("shutdown"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('admin', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def shutdown(self, ctx):
        try:
            log.debug('shutdown command received from "%s"', ctx.author.name)
            started_at = self.bot.command_staff.start_time
            started_at_string = started_at.strftime(self.bot.std_date_time_format)
            online_duration = datetime.utcnow() - started_at

            embed = await make_basic_embed(title='cya!', text='AntiPetros is shutting down.', symbol='shutdown', was_online_since=started_at_string, online_for=await async_seconds_to_pretty_normal(online_duration.total_seconds(), decimal_places=0))
            embed.set_image(url='https://media.discordapp.net/attachments/449481990513754114/785601325329023006/2d1ca5fea58e65277ac5c18788b21d03.gif')
            last_shutdown_message = await ctx.send(embed=embed)
            pickleit({"message_id": last_shutdown_message.id, "channel_id": last_shutdown_message.channel.id}, self.shutdown_message_pickle_file)

        except Exception as error:
            log.error(error, exc_info=False)
        finally:
            await ctx.message.delete()
            await self.bot.close()

    @ commands.command(aliases=get_aliases("list_configs"))
    @ commands.dm_only()
    async def list_configs(self, ctx):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            _embed = discord.Embed(title="Anti Petros Report")
            await add_to_embed_listfield(_embed, 'Available Configs', available_configs.keys(), prefix='-')
            await ctx.send(embed=_embed)

            log.info("config list send to '%s'", ctx.author.name)

    @ commands.command(aliases=get_aliases("config_request"))
    @ commands.dm_only()
    async def config_request(self, ctx, config_name: str = 'all'):
        if ctx.author.id in self.allowed_dm_invoker_ids:
            available_configs = await self.get_available_configs()
            requested_configs = []
            if config_name.casefold() == 'all':
                requested_configs = [conf_file_name for key, conf_file_name in available_configs.items()]

            else:
                _req_config_path = await self._match_config_name(config_name)
                requested_configs.append(os.path.basename(_req_config_path))

            if requested_configs == []:
                # TODO: make as embed
                await ctx.send(f'I was **NOT** able to find a config named `{config_name}`!\nTry again with `all` as argument, or request the available configs with the command `list_configs`')
            else:
                for req_config in requested_configs:
                    _msg = f"Here is the file for the requested config `{req_config}`"
                    _file = await self._config_file_to_discord_file(req_config)
                    # TODO: make as embed
                    await ctx.send(_msg, file=_file)
                log.info("requested configs (%s) send to %s", ", ".join(requested_configs), ctx.author.name)

    @ commands.command(aliases=get_aliases("overwrite_config_from_file"))
    @ commands.dm_only()
    async def overwrite_config_from_file(self, ctx, config_name: str):

        if len(ctx.message.attachments) > 1:
            # TODO: make as embed
            await ctx.send('please only send a single file with the command')
            return
        _file = ctx.message.attachments[0]
        _config_path = await self._match_config_name(config_name)
        if _config_path is None:
            # TODO: make as embed
            await ctx.send(f'could not find a config that fuzzy matches `{config_name}`')
        else:
            await _file.save(_config_path)
            for cfg in self.all_configs:
                cfg.read()
                # TODO: make as embed
            await ctx.send(f'saved your file as `{os.path.basename(_config_path)}`.\n\n_You may have to reload the Cogs or restart the bot for it to take effect!_')

    @ commands.command(aliases=get_aliases("add_to_blacklist"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def add_to_blacklist(self, ctx, user_id: int):
        # TODO: CRITICAL ! CHANGE TO SAVE TO JSON AND MAKE BOT METHOD FOR SAVING BLACKLIST JSON FILE
        user = await self.bot.fetch_user(user_id)
        if user is None:
            # TODO: make as embed
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        if user.bot is True:
            # TODO: make as embed
            await ctx.send("the user you are trying to add is a **__BOT__**!\n\nThis can't be done!")
            return
        current_blacklist = self.bot.blacklisted_users
        current_blacklist.append(user_id)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            # TODO: make as embed
            await user.send(f"***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.notify_contact_member}__** per DM!")
        else:
            # TODO: make as embed
            await user.send(f"You have been put on my __BLACKLIST__, you won't be able to invoke my commands.\n\nIf you think this was done in error or other questions, contact **__{self.bot.notify_contact_member}__** per DM!")
            # TODO: make as embed
        await ctx.send(f"User '{user.name}' with the id '{user.id}' was added to my blacklist, he wont be able to invoke my commands!\n\nI have also notified him by DM of this fact!")

    @ commands.command(aliases=get_aliases("remove_from_blacklist"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def remove_from_blacklist(self, ctx, user_id: int):

        user = await self.bot.fetch_user(user_id)
        if user is None:
            # TODO: make as embed
            await ctx.send(f"Can not find a User with the id '{str(user_id)}'!")
            return
        current_blacklist = self.bot.blacklisted_users
        if user.id not in current_blacklist:
            # TODO: make as embed
            await ctx.send(f"User '{user.name}' with User_id '{user.id}' is currently **__NOT__** in my ***Blacklist***\n and can therefor not be removed from the ***Blacklist***!")
            return

        for index, item in enumerate(current_blacklist):
            if item == user_id:
                to_delete_index = index
                break
        current_blacklist.pop(to_delete_index)
        BASE_CONFIG.set('blacklist', 'user', current_blacklist)
        BASE_CONFIG.save()
        if self.bot.is_debug is True:
            # TODO: make as embed
            await user.send("***THIS IS JUST A TEST, SORRY FOR THE DM BOTHER***\n\nYou have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
        else:
            # TODO: make as embed
            await user.send("You have been **__REMOVED__** from my Blacklist.\n\nYou can again invoke my commands again!")
            # TODO: make as embed
        await ctx.send(f"User '{user.name}' with User_id '{user.id}' was removed from my Blacklist.\n\nHe is now able again, to invoke my commands!")

    @ commands.command(aliases=get_aliases("tell_uptime"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def tell_uptime(self, ctx):

        now_time = datetime.utcnow()
        delta_time = now_time - await self.bot.command_staff.start_time
        seconds = round(delta_time.total_seconds())
        # TODO: make as embed
        await ctx.send(f"__Uptime__ -->\n\t\t| {str(seconds_to_pretty(seconds))}")

    @ commands.command(aliases=get_aliases("delete_msg"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def delete_msg(self, ctx, msg_id: int):

        channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        await message.delete()
        await ctx.message.delete()

    @ commands.command(aliases=get_aliases("write_data"))
    @ commands.is_owner()
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def write_data(self, ctx):
        await gather_data(self.bot)
        await ctx.send(embed=await make_basic_embed(title='Data Collected', text='Data was gathered and written to the assigned files', symbol='save', collected_data='This command only collected fixed data like role_ids, channel_ids,...\n', reason='Data is collected and saved to a json file so to not relying on getting it at runtime, as this kind of data is unchanging', if_it_changes='then this command can just be run again'))

    @ commands.command(aliases=get_aliases("show_command_names"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('test_playground', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('admin', 'allowed_channels')))
    async def show_command_names(self, ctx):

        _out = []

        for cog_name, cog_object in self.bot.cogs.items():
            for command in cog_object.get_commands():
                _out.append('__**' + str(command.name) + '**__' + ': ```\n' + str(command.help).split('\n')[0] + '\n```')
        await self.bot.split_to_messages(ctx, '\n---\n'.join(_out), split_on='\n---\n')

    def __repr__(self):
        return f"{self.name}({self.bot.user.name})"

    def __str__(self):
        return self.__class__.__name__


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AdministrationCog(bot))
