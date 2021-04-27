

# region [Imports]

import os
import inspect
from textwrap import dedent
import subprocess
import shutil
import re
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from discord.ext import commands, tasks
import discord
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson, loadjson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.engine.replacements import auto_meta_info_command, AntiPetrosBaseCog, RequiredFile, RequiredFolder, auto_meta_info_group, AntiPetrosFlagCommand, AntiPetrosBaseCommand, AntiPetrosBaseGroup, CommandCategory

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

PERMISSION_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'permission_data.json')
ROLE_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'role_data.json')
CHANNEL_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'channel_data.json')
CHANNEL_CAT_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'channel_category_data.json')
GENERAL_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'general_data.json')
MEMBERS_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'members_data.json')
ROLE_CHANNEL_DATA_OUTPUT = pathmaker(APPDATA['fixed_data'], 'role_channel_data.json')

# endregion[Constants]


def main_dir_from_git():
    GIT_EXE = shutil.which('git.exe')
    cmd = subprocess.run([GIT_EXE, "rev-parse", "--show-toplevel"], capture_output=True, text=True, shell=True, check=True)
    main_dir = pathmaker(cmd.stdout.rstrip('\n'))
    if os.path.isdir(main_dir) is False:
        raise FileNotFoundError('Unable to locate main dir of project')
    return main_dir


def get_gif(in_command: commands.Command):
    main_dir = main_dir_from_git()
    GIF_FOLDER = pathmaker(main_dir, 'art', 'finished', 'gifs')
    for file in os.scandir(GIF_FOLDER):
        if file.is_file() and file.name.endswith('.gif') and file.name.casefold().startswith(in_command.name.casefold()):
            print(main_dir)
            return pathmaker(pathmaker(file.path).removeprefix(pathmaker(main_dir) + '/'))
    return None


def save_cog_command_data(cog, output_file=None):
    command_json_file = pathmaker(os.getenv('TOPLEVELMODULE'), '../docs/resources/data/command_data.json') if output_file is None else pathmaker(output_file)

    if os.path.isfile(command_json_file) is False:
        writejson({}, command_json_file)

    command_json = loadjson(command_json_file)

    command_json[str(cog)] = {'file_path': pathmaker(inspect.getfile(cog.__class__)).split('site-packages')[-1].strip('/'),
                              'description': dedent(str(inspect.getdoc(cog.__class__))),
                              "commands": {},
                              "state": cog.docattrs.get('is_ready').serialize(),
                              'config_name': cog.config_name}

    for command in cog.get_commands():
        try:

            command_json[str(cog)]["commands"][command.name.strip()] = {"signature": None if command.signature is None else command.signature.replace('<ctx>', '').replace('  ', ' ').strip(),
                                                                        "aliases": command.aliases,
                                                                        "parameter": [param_string for param_string, _ in command.clean_params.items() if param_string != 'ctx'],
                                                                        "checks": [str(check) for check in command.checks],
                                                                        'short_doc': command.short_doc,
                                                                        'usage': command.usage,
                                                                        'description': command.description,
                                                                        'is_hidden': command.hidden,
                                                                        'is_enabled': command.enabled,
                                                                        'qualified_name': command.qualified_name,
                                                                        'help': command.help,
                                                                        'brief': command.brief,
                                                                        'gif': get_gif(command),
                                                                        'example': command.example if hasattr(command, 'example') else None,
                                                                        'is_group': False,
                                                                        'categories': command.categories}
            if isinstance(command, AntiPetrosBaseGroup):
                command_json[str(cog)]["commands"][command.name.strip()]['is_group'] = True
                command_json[str(cog)]["commands"][command.name.strip()]['subcommands'] = {}
                for subcommand_name, subcommand in command.all_commands.items():
                    subcommand_name = subcommand.qualified_name.split(' ')[-1]
                    if subcommand_name not in command_json[str(cog)]["commands"][command.name.strip()]['subcommands']:
                        command_json[str(cog)]["commands"][command.name.strip()]['subcommands'][subcommand_name.strip()] = {"signature": None if subcommand.signature is None else subcommand.signature.replace('<ctx>', '').replace('  ', ' ').strip(),
                                                                                                                            "aliases": subcommand.aliases,
                                                                                                                            "parameter": [param_string for param_string, _ in subcommand.clean_params.items() if param_string != 'ctx'],
                                                                                                                            "checks": [str(check) for check in subcommand.checks],
                                                                                                                            'short_doc': subcommand.short_doc,
                                                                                                                            'usage': subcommand.usage,
                                                                                                                            'description': subcommand.description,
                                                                                                                            'is_hidden': subcommand.hidden,
                                                                                                                            'is_enabled': subcommand.enabled,
                                                                                                                            'qualified_name': subcommand.qualified_name,
                                                                                                                            'help': subcommand.help,
                                                                                                                            'brief': subcommand.brief,
                                                                                                                            'gif': get_gif(command),
                                                                                                                            'example': subcommand.example if hasattr(command, 'example') else None,
                                                                                                                            'categories': command.categories}
        except AttributeError as error:
            print('!' * 25)
            print(command.name)
            print(error)
            print('!' * 25)

    writejson(command_json, command_json_file, indent=4)
    log.debug("commands for %s saved to %s", cog, command_json_file)


async def get_member_data(bot):
    member_data = {"by_roles": {}}
    for role in await bot.antistasi_guild.fetch_roles():
        if '@everyone' not in role.name:
            member_data['by_roles'][role.name] = {mem.name: mem.id for mem in role.members}
    writejson(member_data, MEMBERS_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_general_data(bot):
    general_data = {"antistasi_guild_id": 449481990513754112}
    general_data['owner_id'] = bot.antistasi_guild.owner_id
    general_data['filesize_limit'] = bot.antistasi_guild.filesize_limit
    general_data['filesize_limit_mb'] = bot.antistasi_guild.filesize_limit / (1024 * 1024)
    try:
        general_data['webhooks'] = [webhook.name for webhook in await bot.antistasi_guild.webhooks()]
    except Exception as error:
        log.error(error)
    writejson(general_data, GENERAL_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_role_data(bot):
    role_data = {"role_list": {}, "role_info_list": {}}
    try:
        for role in await bot.antistasi_guild.fetch_roles():
            role_data["role_list"][role.name] = role.id
            role_data["role_info_list"][role.name] = {'position': role.position,
                                                      'mentionable': role.mentionable,
                                                      'permissions': {perm[0]: perm[1] for perm in role.permissions},
                                                      'color': role.color.to_rgb(),
                                                      'create_time': role.created_at.isoformat(timespec='seconds'),
                                                      'mention_string': role.mention}

    except Exception as error:
        log.error(error)
    writejson(role_data, ROLE_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_channel_data(bot):
    channel_dict = {'channel_list': {}, 'category_channels': {}, 'Antipetros_permissions': {}}
    channel_dict['category_channels'] = {cat.name: cat.id for cat in bot.antistasi_guild.categories}

    for channel in bot.antistasi_guild.channels:
        channel_dict['channel_list'][channel.name] = channel.id
        channel_dict['Antipetros_permissions'][channel.name] = {perm[0]: perm[1] for perm in channel.permissions_for(bot.bot_member)}
    writejson(channel_dict, CHANNEL_DATA_OUTPUT, indent=4)


async def get_channel_role_data(bot):
    role_dict = {}
    for role in await bot.antistasi_guild.fetch_roles():
        if '@everyone' not in role.name:
            if role.name not in role_dict:
                role_dict[role.name] = {}
            for channel in bot.antistasi_guild.channels:
                try:
                    role_dict[role.name][channel.name] = {perm[0]: perm[1] for perm in channel.permissions_for(role.members[0])}
                except IndexError:
                    log.error(str([member.name for member in role.members]))
    writejson(role_dict, ROLE_CHANNEL_DATA_OUTPUT, sort_keys=False, indent=4)


async def get_channel_category_data(bot):
    _chan_cat_dict = {}
    for category in bot.antistasi_guild.categories:
        if category.name not in _chan_cat_dict:
            _chan_cat_dict[category.name] = []
        for channel in category.channels:
            _chan_cat_dict[category.name].append(channel.name)
        _chan_cat_dict[category.name] = sorted(list(set(_chan_cat_dict[category.name])))
    writejson(_chan_cat_dict, CHANNEL_CAT_DATA_OUTPUT, sort_keys=False, indent=4)


async def gather_data(bot):
    await get_channel_category_data(bot)
    await get_general_data(bot)
    await get_channel_data(bot)
    await get_role_data(bot)
    await get_member_data(bot)
    await get_channel_role_data(bot)
