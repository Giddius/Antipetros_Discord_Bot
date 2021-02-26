
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from collections import namedtuple

# endregion[Imports]

# for saved links
LINK_DATA_ITEM = namedtuple('LinkDataItem', ['author', 'link_name', 'date_time', 'delete_date_time', 'link'])

# for saved suggestions
SUGGESTION_DATA_ITEM = namedtuple('SuggestionDataItem', ['name', 'message_author', 'reaction_author', 'message', 'time', 'team', 'extra_data'], defaults=(None,))


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


ColorItem = namedtuple('ColorItem', ['name', 'hex', 'hex_alt', 'hsv', 'hsv_norm', 'int', 'rgb', 'rgb_norm', 'discord_color'])


FlagItem = namedtuple('FlagItem', ['name', 'value'])

MemberRoleItem = namedtuple("MemberRoleItem", ['name', 'id'])


GiveAwayEventItem = namedtuple("GiveAwayEventItem", ['title', 'channel_name', 'message_id', 'enter_emoji', 'end_date_time', 'end_message', 'amount_winners', "author_id"])


EmbedFieldItem = namedtuple("EmbedFieldItem", ['name', 'value', "inline"], defaults=(None, None, None))


ListenerContext = namedtuple('ListenerContext', ['message', 'content', 'channel', 'author', 'creation_time', 'reactions', 'attachments'], defaults=([], []))
