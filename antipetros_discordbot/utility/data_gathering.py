

# region [Imports]

# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper

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
