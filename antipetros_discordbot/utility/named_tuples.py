
# region [Imports]

# * Standard Library Imports -->
from collections import namedtuple

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
