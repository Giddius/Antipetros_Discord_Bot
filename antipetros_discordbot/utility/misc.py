# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
import inspect
from asyncio import get_event_loop
from datetime import datetime
from textwrap import dedent
from functools import wraps, partial
from concurrent.futures import ThreadPoolExecutor
from inspect import getfullargspec, getmembers, getargspec, signature, currentframe, getclosurevars
from pprint import pprint

# * Third Party Imports --------------------------------------------------------------------------------->
# * Third Party Imports -->
import discord
from discord.ext import commands
from icecream import ic
# * Gid Imports ----------------------------------------------------------------------------------------->
# * Gid Imports -->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
# * Local Imports -->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writejson, writeit, readit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.data import COMMAND_CONFIG_SUFFIXES, DEFAULT_CONFIG_OPTION_NAMES, DEFAULT_CONFIG_SECTION
from antipetros_discordbot.utility.checks import owner_or_admin
from antipetros_discordbot.utility.enums import CogState

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

SGF = 1024  # SIZE_GENERAL_FACTOR
SIZE_CONV = {'byte': {'factor': SGF**0, 'short_name': 'b'},
             'kilobyte': {'factor': SGF**1, 'short_name': 'kb'},
             'megabyte': {'factor': SGF**2, 'short_name': 'mb'},
             'gigabyte': {'factor': SGF**3, 'short_name': 'gb'},
             'terrabyte': {'factor': SGF**4, 'short_name': 'tb'}}

SIZE_CONV_BY_SHORT_NAME = {'b': 1,
                           'gb': 1073741824,
                           'kb': 1024,
                           'mb': 1048576,
                           'tb': 1099511627776}

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


def save_commands(cog, output_file=None):
    command_json_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/resources/data/commands.json') if output_file is None else pathmaker(output_file)

    if os.path.isfile(command_json_file) is False:
        writejson({}, command_json_file)

    command_json = loadjson(command_json_file)

    command_json[str(cog)] = {'file_path': pathmaker(os.path.abspath(inspect.getfile(cog.__class__))),
                              'description': dedent(str(inspect.getdoc(cog.__class__))),
                              "commands": {},
                              "state": [' | '.join(map(str, CogState.split(cog.docattrs.get('is_ready')[0]))), cog.docattrs.get('is_ready')[1]]
                              }

    for command in cog.get_commands():
        command_json[str(cog)]["commands"][command.name.strip()] = {"signature": command.signature.replace('<ctx>', '').replace('  ', ' ').strip(),
                                                                    "aliases": command.aliases,
                                                                    "parameter": [param_string for param_string, _ in command.clean_params.items() if param_string != 'ctx'],
                                                                    "checks": [str(check).split()[1].split('.')[0] for check in command.checks],
                                                                    'short_doc': command.short_doc,
                                                                    'usage': command.usage,
                                                                    'description': command.description,
                                                                    'is_hidden': command.hidden,
                                                                    'is_enabled': command.enabled,
                                                                    'qualified_name': command.qualified_name}

    writejson(command_json, command_json_file, indent=4)
    log.debug("commands for %s saved to %s", cog, command_json_file)


def make_command_subsection_seperator(command_name):
    command_name = f"{command_name} COMMAND"
    return f'# {command_name.upper().center(75, "-")}'


def generate_base_cogs_config(bot: commands.Bot, output_file=None):
    out_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/resources/prototype_files/standard_cogs_config.ini') if output_file is None else pathmaker(output_file)
    sub_section_seperator = f'# {"_"*75}'
    command_section_seperator = f'# {"COMMANDS".center(75, "-")}'
    listener_section_seperator = f'# {"LISTENER".center(75, "+")}'
    out_lines = [DEFAULT_CONFIG_SECTION]
    for cog_name, cog in bot.cogs.items():
        config_name = cog.config_name
        required_config_data = cog.required_config_data

        out_lines += [f'\n\n[{config_name}]',
                      'default_allowed_dm_ids =',
                      'default_allowed_channels =',
                      'default_allowed_roles =',
                      sub_section_seperator + '\n' + sub_section_seperator,
                      required_config_data]
        for command in cog.get_commands():
            out_lines.append(make_command_subsection_seperator(command.name))
            out_lines.append(f"{command.name}{COMMAND_CONFIG_SUFFIXES.get('enabled')[0]} = {COMMAND_CONFIG_SUFFIXES.get('enabled')[1]}")
            out_lines.append(f"{command.name}{COMMAND_CONFIG_SUFFIXES.get('channels')[0]} = {COMMAND_CONFIG_SUFFIXES.get('channels')[1]}")

            out_lines.append(f"{command.name}{COMMAND_CONFIG_SUFFIXES.get('roles')[0]} = {COMMAND_CONFIG_SUFFIXES.get('roles')[1]}")
            if any(getclosurevars(check).nonlocals.get('in_dm_allowed', False) is True for check in command.checks):
                out_lines.append(f"{command.name}{COMMAND_CONFIG_SUFFIXES.get('dm_ids')[0]} = {COMMAND_CONFIG_SUFFIXES.get('dm_ids')[1]}")
    writeit(out_file, '\n\n'.join(out_lines))


def generate_help_data(cog: commands.Cog, output_file=None):
    help_data_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/resources/data/command_help.json') if output_file is None else pathmaker(output_file)
    if os.path.isfile(help_data_file) is False:
        writejson({}, help_data_file)
    help_data = loadjson(help_data_file)
    cog_name = cog.qualified_name
    if cog_name not in help_data:
        help_data[cog_name] = {}
    help_data[cog_name] = {'description': cog.description,
                           'config_name': cog.config_name,
                           'file_path': pathmaker(os.path.abspath(inspect.getfile(cog.__class__))),
                           'commands': {}}
    for command in cog.get_commands():
        help_data[cog_name]['commands'][command.name.strip()] = {'brief': command.brief,
                                                                 'description': command.description,
                                                                 'usage': command.usage,
                                                                 'help': command.help}
    writejson(help_data, help_data_file)


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


class CogConfigReadOnly():
    cogs_config = ParaStorageKeeper.get_config('cogs_config')
    retriev_map = {str: cogs_config.get,
                   list: cogs_config.getlist,
                   int: cogs_config.getint,
                   bool: cogs_config.getboolean,
                   set: partial(cogs_config.getlist, as_set=True)}

    def __init__(self, config_name):
        self.config_name = config_name

    def __call__(self, key, typus: type = str):
        return self.retriev_map.get(typus)(section=self.config_name, option=key)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config_name={self.config_name})"


def minute_to_second(minutes: int):
    return minutes * 60


def hour_to_second(hours: int):
    return hours * 60 * 60


def day_to_second(days: int):
    return days * 24 * 60 * 60


def datetime_isoformat_to_discord_format(in_data: datetime):

    return in_data.replace(microsecond=0).isoformat()


def make_config_name(name):
    name = split_camel_case_string(name).replace('Cog', '').strip().replace(' ', '_').casefold()

    return name


def is_even(number: int):
    return not number & 1
