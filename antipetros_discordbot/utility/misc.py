# * Standard Library Imports -->
# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from io import BytesIO
from asyncio import get_event_loop
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance
from functools import wraps, partial
from concurrent.futures import ThreadPoolExecutor
from inspect import getclosurevars
import json
from typing import Awaitable, Iterable, Mapping, Tuple, TypeVar, Iterable, Dict, Union
# * Third Party Imports --------------------------------------------------------------------------------->
# * Third Party Imports -->
from validator_collection import validators
import validator_collection
import discord
from discord.ext import commands, tasks
from aiohttp.client_exceptions import ClientConnectionError
from colormap.colors import hex2rgb, rgb2hsv

# * Gid Imports ----------------------------------------------------------------------------------------->
# * Gid Imports -->
import gidlogger as glog
from antipetros_discordbot.utility.pygment_styles import DraculaStyle, GithubStyle
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name, get_all_lexers, guess_lexer
from pygments.formatters import HtmlFormatter, ImageFormatter
from pygments.styles import get_style_by_name, get_all_styles
from pygments.filters import get_all_filters
# * Local Imports --------------------------------------------------------------------------------------->
# * Local Imports -->
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker, writeit, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.data import COMMAND_CONFIG_SUFFIXES, DEFAULT_CONFIG_SECTION
from antipetros_discordbot.utility.enums import CogMetaStatus

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
_LOOP = None
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
NANOSECONDS_FACTOR = 1 / 1000000000
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


def alt_seconds_to_pretty(seconds: int, decimal_places: int = 1, separator: str = ", ", last_separator: str = None, shorten_name_to: int = None):
    last_separator = separator if last_separator is None else last_separator
    out_string = ''
    parts = []
    rest = seconds
    for name, factor in FACTORS.items():
        sub_result, rest = divmod(rest, factor)
        if sub_result != 0:
            if shorten_name_to is not None:
                name = name[0:shorten_name_to]
            parts.append(f"{str(int(round(sub_result, ndigits=decimal_places)))} {name}")
    for index, part in enumerate(parts):
        if index == 0:
            out_string += f"{part}"
        elif index != (len(parts) - 1):
            out_string += f"{separator}{part}"
        else:
            out_string += f"{last_separator}{part}"

    return out_string.strip()


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


R = TypeVar("R")


def async_to_sync(func: Awaitable[R]) -> R:
    '''Wraps `asyncio.run` on an async function making it sync callable.'''
    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"{func} is not a coroutine function")

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


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


async def generate_bot_data(bot, production_bot):
    bot_info_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/resources/data/bot_info.json')
    attrs_to_get = ['description']
    bot_info = {}
    for attr in attrs_to_get:
        bot_info[attr] = getattr(bot, attr)
    bot_info['display_name'] = production_bot.display_name
    bot_info['guild'] = bot.guilds[0].name
    bot_info['intents'] = dict(bot.intents)
    bot_info['avatar_url'] = str(production_bot.avatar_url)
    bot_info['invite_url'] = bot.antistasi_invite_url
    bot_info['role_names'] = [role.name for role in production_bot.roles if 'everyone' not in role.name.casefold()]
    bot_info['amount_cogs'] = len([cog for cog in bot.cogs if cog.casefold() != 'generaldebugcog'])
    bot_info['amount_commands'] = len([command for command in bot.commands if str(command.cog).casefold() != 'generaldebugcog'])

    writejson(bot_info, bot_info_file)


def generate_help_data(cog: commands.Cog, output_file=None):
    if CogMetaStatus.FOR_DEBUG in CogMetaStatus.split(cog.docattrs['is_ready'][0]):
        return
    help_data_file = pathmaker(APPDATA['documentation'], 'command_meta_data.json') if output_file is None else pathmaker(output_file)
    if os.path.isfile(help_data_file) is False:
        writejson({}, help_data_file)
    help_data = loadjson(help_data_file)

    for command in cog.get_commands():
        help_data[command.name.strip().casefold()] = {'brief': command.brief,
                                                      'description': command.description,
                                                      'usage': command.usage,
                                                      'help': command.help,
                                                      'hidden': command.hidden,
                                                      'brief': command.brief,
                                                      'short_doc': command.short_doc}

    writejson(help_data, help_data_file)


async def async_load_json(json_file):
    global _LOOP
    if _LOOP is None:
        _LOOP = asyncio.get_event_loop()
    return await _LOOP.run_in_executor(None, loadjson, json_file)


async def async_write_json(data, json_file):
    global _LOOP
    if _LOOP is None:
        _LOOP = asyncio.get_event_loop()
    return await _LOOP.run_in_executor(None, writejson, data, json_file)


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


def split_camel_case_string(string, filler=' '):
    _out = []
    for char in string:
        if char == char.upper():
            char = filler + char
        _out.append(char)
    return ''.join(_out).strip(filler)


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


def ns_to_s(ns: int):
    return ns * NANOSECONDS_FACTOR


def datetime_isoformat_to_discord_format(in_data: datetime):

    return in_data.replace(microsecond=0).isoformat()


def make_config_name(name):
    name = split_camel_case_string(name).replace('Cog', '').strip().replace(' ', '_').casefold()

    return name


def is_even(number: int):
    return not number & 1


async def delete_specific_message_if_text_channel(message: discord.Message, delay: int = None):
    try:
        if message.channel.type is discord.ChannelType.text:
            await message.delete(delay=delay)
    except discord.errors.HTTPException as error:
        log.error(error.text)


async def delete_message_if_text_channel(ctx: commands.Context, delay: int = None):
    try:
        if ctx.channel.type is discord.ChannelType.text:
            await ctx.message.delete(delay=delay)
    except discord.errors.HTTPException as error:
        log.error(error.text)


def fix_url_prefix(in_url: str):
    if not in_url.startswith('http://') and not in_url.startswith('https://'):
        in_url = 'https://' + in_url
    return in_url


def check_if_url(possible_url: str):
    """
    checks if input `possible_url` is and valid url.

    Appends "https://" in front of it beforehand. (maybe not necessary).

    Args:
        possible_url `str`: The string to check.

    Returns:
        `bool`: `True` if it is and valid url.
    """
    possible_url = fix_url_prefix(possible_url)
    try:
        validators.url(possible_url)
        return True
    except validator_collection.errors.InvalidURLError:
        return False


async def url_is_alive(bot, url, check_if_github=False):
    try:
        async with bot.aio_session.get(url) as _response:
            if check_if_github is True and _response.headers.get('Server') != 'GitHub.com':
                return False
            return _response.status_code != 404
    except ClientConnectionError:
        return False


async def dict_from_attached_json(attachment: discord.Attachment):
    if not attachment.filename.endswith('.json'):
        # TODO: Custom Error
        raise TypeError("needs to be json file")
    byte_data = await attachment.read()
    data = byte_data.decode('utf-8')
    return json.loads(data)


async def antipetros_repo_rel_path(in_path: str):
    in_path = pathmaker(in_path).casefold()
    in_path_parts = in_path.split('/')
    while in_path_parts[0] != 'antipetros_discordbot':
        _ = in_path_parts.pop(0)
    return pathmaker(*in_path_parts)


def sync_antipetros_repo_rel_path(in_path: str):
    in_path = pathmaker(in_path)
    in_path_parts = in_path.split('/')
    while in_path_parts[0] != 'antipetros_discordbot':
        _ = in_path_parts.pop(0)
    return pathmaker(*in_path_parts)


async def async_dict_items_iterator(in_dict: Mapping):
    for key, value in in_dict.items():
        yield key, value
        await asyncio.sleep(0)


async def async_list_iterator(in_list: Iterable):
    for item in in_list:
        yield item
        await asyncio.sleep(0)


async def async_write_it(in_file, in_data, append=False, in_encoding='utf-8', in_errors=None):
    global _LOOP
    if _LOOP is None:
        _LOOP = asyncio.get_event_loop()
    await _LOOP.run_in_executor(None, writeit, in_file, in_data, append, in_encoding, in_errors)


def highlight_print(in_data, highlight_level: int = 1):
    seperators = {0: "#" * 10,
                  1: "*" * 10,
                  2: "!" * 10,
                  3: "+-" * 5}
    print("")
    for i in range(highlight_level):
        print(seperators.get(i))
    print(in_data)
    for i in reversed(range(highlight_level)):
        print(seperators.get(i))
    print("")


async def make_other_source_code_images(file_content: str, lexer: str = 'guess', style: str = 'dracula'):

    lexer_map = {'guess': guess_lexer(file_content),
                 'python': PythonLexer(),
                 'ini': get_lexer_by_name('INI')}
    style_map = {'dracula': DraculaStyle,
                 'github': GithubStyle}

    lexer = lexer_map.get(lexer.casefold())

    image = await asyncio.to_thread(highlight, file_content, lexer, ImageFormatter(style=style_map.get(style.casefold()),
                                                                                   font_name='Fira Code',
                                                                                   line_number_bg="#2f3136",
                                                                                   line_number_fg="#ffffff",
                                                                                   line_number_chars=3,
                                                                                   line_pad=5,
                                                                                   font_size=20,
                                                                                   line_number_bold=True))
    return image


async def make_other_source_code_images_to_pil(file_content: str, lexer: str = 'guess', style: str = 'dracula'):

    lexer_map = {'guess': guess_lexer(file_content),
                 'python': PythonLexer(),
                 'ini': get_lexer_by_name('INI')}
    style_map = {'dracula': DraculaStyle,
                 'github': GithubStyle}

    lexer = lexer_map.get(lexer.casefold())
    with BytesIO() as bitey:
        image = await asyncio.to_thread(highlight, file_content, lexer, ImageFormatter(style=style_map.get(style.casefold()),
                                                                                       font_name='Fira Code',
                                                                                       line_number_bg="#2f3136",
                                                                                       line_number_fg="#ffffff",
                                                                                       line_number_chars=3,
                                                                                       line_pad=5,
                                                                                       font_size=20,
                                                                                       line_number_bold=True), outfile=bitey)
        bitey.seek(0)
        pil_image = Image.open(bitey)
        pil_image.load()

    height, width = pil_image.size
    while height > 5000 or width > 5000:
        pil_image = pil_image.resize((height // 2, width // 2))
        height, width = pil_image.size
    image_bytes = pil_image.tobytes()
    return image_bytes


def hex_to_rgb(color: str, normalized: bool = False):
    return hex2rgb(color, normalise=normalized)


def hex_to_int(color: str):
    return int(color.removeprefix('#'), 16)


def rgb_to_hsv(color: Tuple[int], normalized: bool = False):
    return rgb2hsv(*color, normalised=normalized)


def hex_to_hex_alt(color: str):
    return color.replace('#', '0x')


def datetime_is_aware(in_datetime: datetime) -> bool:
    return (
        in_datetime.tzinfo is not None and in_datetime.tzinfo.utcoffset(in_datetime) is not None
    )


def get_github_line_link(base_url: str, file_path, source_lines):
    rel_path = sync_antipetros_repo_rel_path(file_path)
    start_line_number = source_lines[1]
    code_length = len(source_lines[0])
    full_path = base_url + rel_path + f'#L{start_line_number}-L{start_line_number+code_length-1}'
    return full_path


def help_to_file(in_object, out_file=None):
    """
    redirects the output of the `help` built-in function to a file.

    https://gist.github.com/abingham/e19cfd042fefcd11ba60

    Args:
        in_object (`object`): the object to use as argument for `help()`
        out_file (`str`, optional): filepath where the output should be redirected to. Defaults to `[class_name of the object]_help.txt`.
    """
    out_file = f'{in_object.__class__.__name__}_help.txt' if out_file is None else pathmaker(out_file)
    import sys

    # Temporarily redirect stdout to a StringIO.
    stdout = sys.stdout
    with open('helpy.txt', 'w') as f:
        sys.stdout = f
        help(in_object)

        # Don't forget to reset stdout!
        sys.stdout = stdout


def loop_starter(task_loop: tasks.Loop):
    if task_loop.is_running() is False:
        task_loop.start()


async def async_loop_starter(task_loops: Dict[str, tasks.Loop]):
    for task_loop_name, task_loop in task_loops.items():
        if task_loop.is_running() is False:
            await asyncio.sleep(0, task_loop.start())
            log.info("Loop %s was started", task_loop_name)


def loop_stopper(task_loop: tasks.Loop):
    if task_loop.is_running() is True:
        task_loop.stop()
