

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
import logging
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union, Iterable
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# * Third Party Imports -->

import discord
from discord.ext import commands, tasks


# * Gid Imports -->

import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.exceptions import MissingAttachmentError, NotAllowedChannelError, NotNecessaryRole, IsNotTextChannelError
from antipetros_discordbot.utility.misc import casefold_list, casefold_contains
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]


# endregion[Constants]


def in_allowed_channels(allowed_channels: Iterable):
    def predicate(ctx):
        return ctx.channel.name in allowed_channels if not isinstance(ctx.channel, discord.DMChannel) else False
    return commands.check(predicate)


def log_invoker(logger):
    def predicate(ctx):
        if BASE_CONFIG.getboolean('general_settings', 'is_debug'):
            logger.info("command '%s' as '%s' -- invoked by: name: '%s', id: %s -- in channel: '%s' -- raw invoking message: '%s'",
                        ctx.command.name, ctx.invoked_with, ctx.author.name, ctx.author.id, ctx.channel.name, ctx.message.content)
        else:
            logger.info("command '%s' as '%s' -- invoked by: name: '%s' -- in channel: '%s' -- args used: %s",
                        ctx.command.name, ctx.invoked_with, ctx.author.name, ctx.channel.name, ctx.args)
        return True
    return commands.check(predicate)


def purge_check_from_user(user_id: int):

    def is_from_user(message):
        return message.author.id == user_id
    return is_from_user


def purge_check_contains(word: str, case_sensitive=False):
    def contains_in_content(message):
        content = message.content
        check_word = word
        if case_sensitive is False:
            content = message.content.casefold()
            check_word = word.casefold()
        return check_word in content.split()
    return contains_in_content


def purge_check_is_bot():
    def message_is_from_bot(message):
        return message.author.bot
    return message_is_from_bot


def purge_check_always_true():
    def always_true(message):
        return True
    return always_true


def purge_check_always_false():
    def always_false(message):
        return False
    return always_false


PURGE_CHECK_TABLE = {'is_bot': purge_check_is_bot,
                     'contains': purge_check_contains,
                     'from_user': purge_check_from_user,
                     'all': purge_check_always_true}


def has_attachments(min_amount_attachments: int = 1):
    def predicate(ctx):
        if len(ctx.message.attachments) >= min_amount_attachments:
            return True
        else:
            raise MissingAttachmentError(ctx, min_amount_attachments)

    return commands.check(predicate)


def is_not_giddi(ctx):
    if ctx.author.name == 'Giddi':
        return False
    return True


def allowed_channel_and_allowed_role_no_dm(config_name: str):
    def predicate(ctx):
        allowed_channels = COGS_CONFIG.getlist(config_name, "allowed_channels", as_set=True, casefold_items=True)
        allowed_roles = COGS_CONFIG.getlist(config_name, "allowed_roles", as_set=True, casefold_items=True)
        channel = ctx.channel.name
        channel_type = ctx.channel.type
        author = ctx.author.name
        roles = ctx.author.roles
        if channel.casefold() not in allowed_channels:
            raise NotAllowedChannelError(ctx, COGS_CONFIG.getlist(config_name, "allowed_channels"))
        if channel_type is not discord.ChannelType.text:
            raise IsNotTextChannelError(ctx, channel_type)
        if all(role.name.casefold() not in allowed_roles for role in roles):
            raise NotNecessaryRole(ctx, COGS_CONFIG.getlist(config_name, "allowed_roles"))
        return True
    return commands.check(predicate)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
