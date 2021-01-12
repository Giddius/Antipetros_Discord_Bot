from functools import wraps, partial
from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
import os
from textwrap import dedent
import inspect
import discord
from pprint import pprint, pformat
from antipetros_discordbot.utility.gidtools_functions import pathmaker, loadjson, writejson, readit, readbin, writeit, work_in, writebin
import gidlogger as glog
from datetime import datetime
import sys


log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


SGF = 1024  # SIZE_GENERAL_FACTOR
SIZE_CONV = {'byte': {'factor': SGF**0, 'short_name': 'b'},
             'kilobyte': {'factor': SGF**1, 'short_name': 'kb'},
             'megabyte': {'factor': SGF**2, 'short_name': 'mb'},
             'gigabyte': {'factor': SGF**3, 'short_name': 'gb'},
             'terrabyte': {'factor': SGF**4, 'short_name': 'tb'}}


STANDARD_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

SECOND_FACTOR = 1
MINUTE_FACTOR = SECOND_FACTOR * 60
HOUR_FACTOR = MINUTE_FACTOR * 60

DAY_FACTOR = HOUR_FACTOR * 24
WEEK_FACTOR = DAY_FACTOR * 7
MONTH_FACTOR = DAY_FACTOR * 30
YEAR_FACTOR = DAY_FACTOR * 365

FACTORS = {'years': YEAR_FACTOR, 'months': MONTH_FACTOR, 'weeks': WEEK_FACTOR, 'days': DAY_FACTOR, 'hours': HOUR_FACTOR, 'minutes': MINUTE_FACTOR, 'seconds': SECOND_FACTOR}
EXECUTOR = ThreadPoolExecutor(thread_name_prefix='Thread', max_workers=4)
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
_IMPORTANT_EVENTS = list(set(['on_connect',
                              'on_disconnect',
                              'on_ready',
                              'on_typing',
                              'on_message',
                              'on_message_delete',
                              'on_raw_message_delete',
                              'on_message_edit',
                              'on_raw_message_edit',
                              'on_reaction_add',
                              'on_raw_reaction_add',
                              'on_raw_reaction_remove',
                              'on_member_join',
                              'on_member_remove',
                              'on_member_update',
                              'on_member_ban',
                              'on_member_unban']))
EVENTS = sorted(_IMPORTANT_EVENTS) + list(set(['on_shard_disconnect',
                                               'on_shard_ready',
                                               'on_resumed',
                                               'on_shard_resumed',
                                               'on_raw_bulk_message_delete',
                                               'on_reaction_clear',
                                               'on_raw_reaction_clear',
                                               'on_reaction_clear_emoji',
                                               'on_raw_reaction_clear_emoji',
                                               'on_private_channel_delete',
                                               'on_private_channel_create',
                                               'on_private_channel_update',
                                               'on_private_channel_pins_update',
                                               'on_guild_channel_delete',
                                               'on_guild_channel_create',
                                               'on_guild_channel_update',
                                               'on_guild_channel_pins_update',
                                               'on_guild_integrations_update',
                                               'on_webhooks_update',
                                               'on_user_update',
                                               'on_guild_join',
                                               'on_guild_remove',
                                               'on_guild_update',
                                               'on_guild_role_create',
                                               'on_guild_role_delete',
                                               'on_guild_role_update',
                                               'on_guild_emojis_update',
                                               'on_guild_available',
                                               'on_guild_unavailable',
                                               'on_voice_state_update',
                                               'on_invite_create',
                                               'on_invite_delete',
                                               'on_group_join',
                                               'on_group_remove',
                                               'on_relationship_add',
                                               'on_relationship_remove',
                                               'on_relationship_update']))


def seconds_to_pretty(seconds: int, decimal_places: int = 1):
    out_string = ''
    rest = seconds
    for name, factor in FACTORS.items():
        sub_result, rest = divmod(rest, factor)
        if sub_result != 0:
            out_string += f"**{name.title()}:** {str(int(round(sub_result,ndigits=decimal_places)))} | "
    return out_string


async def async_seconds_to_pretty_normal(seconds: int, decimal_places: int = 1):
    out_string = ''
    rest = seconds
    for name, factor in FACTORS.items():
        sub_result, rest = divmod(rest, factor)
        if sub_result != 0:
            out_string += f"{str(int(round(sub_result,ndigits=decimal_places)))} {name.lower()} "
    return out_string.strip()


def date_today():
    return datetime.utcnow().strftime("%Y-%m-%d")


async def async_date_today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def sync_to_async(_func):
    @wraps(_func)
    def wrapped(*args, **kwargs):
        loop = get_event_loop()
        func = partial(_func, *args, **kwargs)
        return loop.run_in_executor(executor=EXECUTOR, func=func)
    return wrapped


def save_commands(cog):
    command_json_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/commands.json')
    command_json = loadjson(command_json_file)
    command_json[str(cog)] = {'file_path': pathmaker(os.path.abspath(inspect.getfile(cog.__class__))),
                              'description': dedent(str(inspect.getdoc(cog.__class__))),
                              "commands": {}}
    for command in cog.get_commands():
        command_json[str(cog)]["commands"][command.name.strip()] = {"signature": command.signature.replace('<ctx>', '').replace('  ', ' ').strip(),
                                                                    "aliases": command.aliases,
                                                                    "parameter": [param_string for param_string, _ in command.clean_params.items() if param_string != 'ctx'],
                                                                    "checks": [str(check).split()[1].split('.')[0] for check in command.checks]}
    writejson(command_json, command_json_file, indent=4)
    log.debug("commands for %s saved to %s", cog, command_json_file)


async def async_load_json(json_file):
    return loadjson(json_file)


async def image_to_url(image_path):
    _name = os.path.basename(image_path).replace('_', '').replace(' ', '')
    _file = discord.File(image_path, _name)
    _url = f"attachment://{_name}"
    return _url, _file


def color_hex_embed(color_string):
    return int(color_string, base=16)


def check_if_int(data):
    if not isinstance(data, str):
        data = str(data).strip()
    if data.isdigit():
        return int(data)

    return data


async def async_split_camel_case_string(string):
    _out = []
    for char in string:
        if char == char.upper():
            char = ' ' + char
        _out.append(char)
    return ''.join(_out).strip()


def split_camel_case_string(string):
    _out = []
    for char in string:
        if char == char.upper():
            char = ' ' + char
        _out.append(char)
    return ''.join(_out).strip()


def save_bin_file(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def _check_convert_value_type(value):
    try:
        _out = int(value)
    except ValueError:
        if value == 'True':
            _out = True
        elif value == 'False':
            _out = False
        else:
            _out = value
    return _out


async def handle_arguments_string(argument_string):
    raw_arguments = argument_string.split('|')
    raw_arguments = list(map(lambda x: x.strip(), raw_arguments))
    arg_arguments = []
    kwarg_arguments = {}
    for raw_argument in raw_arguments:
        if '=' in raw_argument:
            key, value = raw_argument.split('=')
            value = _check_convert_value_type(value.strip())
            kwarg_arguments[key.strip()] = value
        else:
            value = _check_convert_value_type(raw_argument.strip())
            arg_arguments.append(value)
    return arg_arguments, kwarg_arguments


EPSILON = sys.float_info.epsilon  # Smallest possible difference.


def convert_to_rgb(minval, maxval, val, colors):

    i_f = float(val - minval) / float(maxval - minval) * (len(colors) - 1)

    i, f = int(i_f // 1), i_f % 1

    if f < EPSILON:
        return colors[i]
    else:
        (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i + 1]
        return int(r1 + f * (r2 - r1)), int(g1 + f * (g2 - g1)), int(b1 + f * (b2 - b1))


def casefold_list(in_list: list):

    def casefold_item(item):
        return item.casefold()

    return list(map(casefold_item, in_list))


def casefold_contains(query, data):
    return query.casefold() in casefold_list(data)
