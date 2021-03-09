
COMMAND_CONFIG_SUFFIXES = {'enabled': ('_enabled', True), 'channels': ('_allowed_channels', ''), 'roles': ('_allowed_roles', ''), 'dm_ids': ('_allowed_dm_ids', '')}


DEFAULT_CONFIG_OPTION_NAMES = {'dm_ids': 'default_allowed_dm_ids', 'channels': 'default_allowed_channels', 'roles': 'default_allowed_roles'}


COG_CHECKER_ATTRIBUTE_NAMES = {'dm_ids': "allowed_dm_ids", 'channels': 'allowed_channels', 'roles': 'allowed_roles'}


COG_NEEDED_ATTRIBUTES = ['on_ready_setup', 'update', 'config_name', 'docattrs', 'required_config_data', 'support', 'allowed_channels', 'allowed_dm_ids', 'allowed_roles']


DEFAULT_CONFIG_SECTION = """# settings here are used if the options are not specified in the sections
[DEFAULT]

# the default roles that are allowed to invoke commands
# as comma seperated list
default_allowed_roles = Dev Helper, Admin, Dev Team

# default allowed channels, set to testing so if i forgot to specify a channel it at least is confined to testing, comma seperated list
default_allowed_channels = bot-testing

# default role that is allowed to delete data, ie = delete the save suggestion database and so on, also set so in worst case it defaults to admin
# - as comma seperated list cave
delete_all_allowed_roles = Admin, Back End Team

# member to contact mostly for bot related stuff, if someone thinks his blacklist is actually a bug or so.
notify_contact_member = Giddi

# default roles for elevated commands if there are ones
# -- as comma seperated list
allowed_elevated_roles = Admin

# list of user ids that are allowed to invoke restriced (but not admin) dm commands, needs to be and id list as in dms there are no roles
# --- as comma seperated list
# currently --> chubchub, vlash
default_allowed_in_dms = 413109712695984130, 122348088319803392

# from here on these are cog specific settings, a section is the config name for an cog ie = "purge_message_cog" --> [purge_message]
# ----------------------------------------------------------------------------------------------------------------------------------
"""