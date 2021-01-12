
# region [Imports]

# * Standard Library Imports -->
from collections import namedtuple

import discord
from discord.ext import commands
from discord import File, Embed
# endregion[Imports]

# for saved links
LINK_DATA_ITEM = namedtuple('LinkDataItem', ['author', 'link_name', 'date_time', 'delete_date_time', 'link'])

# for saved suggestions
SUGGESTION_DATA_ITEM = namedtuple('SuggestionDataItem', ['name', 'message_author', 'reaction_author', 'message', 'time', 'extra_data'], defaults=(None,))


# for templates
NEW_COG_ITEM = namedtuple('NewCogItem', ['name', 'absolute_location', 'import_location', 'config_name', 'all_com_attr', 'all_loops', 'all_listeners', 'all_commands', 'extra_imports', 'code'])
NEW_COMMAND_ITEM = namedtuple('NewCommandItem', ['name', 'code'])
NEW_LISTENER_ITEM = namedtuple('NewListenerItem', ['name', 'event_name', 'code'])
NEW_LOOP_ITEM = namedtuple('NewLoopItem', ['name', 'all_attributes', 'code'])


# for timezones
COUNTRY_ITEM = namedtuple('CountryItem', ['id', 'name', 'code', 'timezone'])
CITY_ITEM = namedtuple('TimeZoneItem', ['id', 'continent', 'name', 'timezone'])

# for feature suggestion
FeatureSuggestionItem = namedtuple("FeatureSuggestionItem", ['author_name', 'author_nick', 'author_id', 'author_roles', 'author_top_role', 'author_joined_at', 'send_at', 'message', 'extra_data_path'], defaults=(None,))

# Me
CreatorMember = namedtuple("CreatorMember", ['name', 'id', 'member_object', 'user_object'], defaults=(None, None))


# for performance

LatencyMeasurement = namedtuple("LatencyMeasurement", ['date_time', 'latency'])

MemoryUsageMeasurement = namedtuple("MemoryUsageMeasurement", ["date_time", "total", "absolute", "as_percent", 'is_warning', 'is_critical'], defaults=(False, False))


InvokedCommandsDataItem = namedtuple("InvokedCommandsDataItem", ['name', 'date', 'data'])


NewCommandStaffItem = namedtuple("NewCommandStaffItem", ['name'])


StartupMessageInfo = namedtuple('StartupMessageInfo', ['channel_id', 'message'])


MovieQuoteItem = namedtuple('MovieQuoteItem', ["quote", "movie", "type", "year"])


RegexItem = namedtuple('RegexItem', ['name', 'raw', 'compiled'], defaults=(None,))


ColorItem = namedtuple('ColorItem', ['name', 'hex', 'hex_alt', 'hsv', 'hsv_norm', 'int', 'rgb', 'rgb_norm'])


FlagItem = namedtuple('FlagItem', ['name', 'value'])
