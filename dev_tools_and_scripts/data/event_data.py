# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, auto

# EVENT_MAPPING = {"on_connect": (),
#                  "on_shard_connect": (("shard_id", "int"),),
#                  "on_disconnect": (),
#                  "on_shard_disconnect": (("shard_id", "int"),),
#                  "on_ready": (),
#                  "on_shard_ready": (("shard_id", "int"),),
#                  "on_resumed": (),
#                  "on_shard_resumed": (("shard_id", "int"),),
#                  "on_socket_raw_receive": (("msg", "Union[bytes, str]"),),
#                  "on_socket_raw_send": (("payload", "Union[bytes, str]"),),
#                  "on_typing": (("channel", "abc.Messageable"), ("user", "Union[discord.User, discord.Member]"), ("when", "datetime")),
#                  "on_message": (("message", "discord.Message"),),
#                  "on_message_delete": (("message", "discord.Message"),),
#                  "on_bulk_message_delete": (("messages", "List[discord.Message]"),),
#                  "on_raw_message_delete": (("payload", "discord.RawMessageDeleteEvent"),),
#                  "on_raw_bulk_message_delete": (("payload", "discord.RawMessageDeleteEvent"),),
#                  "on_message_edit": (("before", "discord.Message"), ("after", "discord.Message")),
#                  "on_raw_message_edit": (("payload", "discord.RawMessageUpdateEvent"),),
#                  "on_reaction_add": (("reaction", "discord.Reaction"), ("user", "Union[discord.User, discord.Member]")),
#                  "on_raw_reaction_add": (("payload", "discord.RawReactionActionEvent"),),
#                  "on_reaction_remove": (("reaction", "discord.Reaction"), ("user", "Union[discord.User, discord.Member]")),
#                  "on_raw_reaction_remove": (("payload", "discord.RawReactionActionEvent"),),
#                  "on_reaction_clear": (("message", "discord.Message"), ("reactions", "List[discord.Reaction]")),
#                  "on_raw_reaction_clear": (("payload", "discord.RawReactionClearEvent"),),
#                  "on_reaction_clear_emoji": (("reaction", "discord.Reaction"),),
#                  "on_raw_reaction_clear_emoji": (("payload", "discord.RawReactionClearEmojiEvent"),),
#                  "on_private_channel_delete": (("channel", "discord.abc.PrivateChannel"),),
#                  "on_private_channel_create": (("channel", "discord.abc.PrivateChannel"),),
#                  "on_private_channel_update": (("before", "discord.GroupChannel"), ("after", "discord.GroupChannel")),
#                  "on_private_channel_pins_update": (("channel", "discord.GroupChannel"), ("last_pin", "datetime")),
#                  "on_guild_channel_delete": (("channel", "discord.abc.GuildChannel"),),
#                  "on_guild_channel_create": (("channel", "discord.abc.GuildChannel"),),
#                  "on_guild_channel_update": (("before", "discord.abc.GuildChannel"), ("after", "discord.abc.GuildChannel")),
#                  "on_guild_channel_pins_update": (("channel", "discord.abc.GuildChannel"), ("last_pin", "datetime")),
#                  "on_guild_integrations_update": (("guild", "discord.Guild"),),
#                  "on_webhooks_update": (("channel", "discord.abc.GuildChannel"),),
#                  "on_member_join": (("member", "discord.Member"),),
#                  "on_member_remove": (("member", "discord.Member"),),
#                  "on_member_update": (("before", "discord.Member"), ("after", "discord.Member")),
#                  "on_user_update": (("before", "discord.User"), ("after", "discord.User")),
#                  "on_guild_join": (("guild", "discord.Guild"),),
#                  "on_guild_remove": (("guild", "discord.Guild"),),
#                  "on_guild_update": (("guild", "discord.Guild"), ("guild", "discord.Guild")),
#                  "on_guild_role_create": (("role", "discord.Role"),),
#                  "on_guild_role_delete": (("role", "discord.Role"),),
#                  "on_guild_role_update": (("role", "discord.Role"), ("role", "discord.Role")),
#                  "on_guild_emojis_update": (("guild", "discord.Guild"), ("before", "Sequence[discord.Emoji]"), ("after", "Sequence[discord.Emoji]")),
#                  "on_guild_available": (("guild", "discord.Guild"),),
#                  "on_guild_unavailable": (("guild", "discord.Guild"),),
#                  "on_voice_state_update": (("member", "discord.Member"), ("before", "discord.VoiceState"), ("after", "discord.VoiceState")),
#                  "on_member_ban": (("guild", "discord.Guild"), ("user", "Union[discord.User,discord.Member]")),
#                  "on_member_unban": (("guild", "discord.Guild"), ("user", "discord.User")),
#                  "on_invite_create": (("invite", "discord.Invite"),),
#                  "on_invite_delete": (("invite", "discord.Invite"),),
#                  "on_group_join": (("channel", "discord.GroupChannel"), ("user", "discord.User")),
#                  "on_group_remove": (("channel", "discord.GroupChannel"), ("user", "discord.User")),
#                  "on_relationship_add": (("relationship", "discord.Relationship"),),
#                  "on_relationship_remove": (("relationship", "discord.Relationship"),),
#                  "on_relationship_update": (("before", "discord.Relationship"), ("after", "discord.Relationship"))}


class Events(Enum):
    on_connect = auto()
    on_shard_connect = auto()
    on_disconnect = auto()
    on_shard_disconnect = auto()
    on_ready = auto()
    on_shard_ready = auto()
    on_resumed = auto()
    on_shard_resumed = auto()
    on_socket_raw_receive = auto()
    on_socket_raw_send = auto()
    on_typing = auto()
    on_message = auto()
    on_message_delete = auto()
    on_bulk_message_delete = auto()
    on_raw_message_delete = auto()
    on_raw_bulk_message_delete = auto()
    on_message_edit = auto()
    on_raw_message_edit = auto()
    on_reaction_add = auto()
    on_raw_reaction_add = auto()
    on_reaction_remove = auto()
    on_raw_reaction_remove = auto()
    on_reaction_clear = auto()
    on_raw_reaction_clear = auto()
    on_reaction_clear_emoji = auto()
    on_raw_reaction_clear_emoji = auto()
    on_private_channel_delete = auto()
    on_private_channel_create = auto()
    on_private_channel_update = auto()
    on_private_channel_pins_update = auto()
    on_guild_channel_delete = auto()
    on_guild_channel_create = auto()
    on_guild_channel_update = auto()
    on_guild_channel_pins_update = auto()
    on_guild_integrations_update = auto()
    on_webhooks_update = auto()
    on_member_join = auto()
    on_member_remove = auto()
    on_member_update = auto()
    on_user_update = auto()
    on_guild_join = auto()
    on_guild_remove = auto()
    on_guild_update = auto()
    on_guild_role_create = auto()
    on_guild_role_delete = auto()
    on_guild_role_update = auto()
    on_guild_emojis_update = auto()
    on_guild_available = auto()
    on_guild_unavailable = auto()
    on_voice_state_update = auto()
    on_member_ban = auto()
    on_member_unban = auto()
    on_invite_create = auto()
    on_invite_delete = auto()
    on_group_join = auto()
    on_group_remove = auto()
    on_relationship_add = auto()
    on_relationship_remove = auto()
    on_relationship_update = auto()


EVENT_MAPPING = {Events.on_connect: (),
                 Events.on_shard_connect: (('shard_id', 'int'),),
                 Events.on_disconnect: (),
                 Events.on_shard_disconnect: (('shard_id', 'int'),),
                 Events.on_ready: (),
                 Events.on_shard_ready: (('shard_id', 'int'),),
                 Events.on_resumed: (),
                 Events.on_shard_resumed: (('shard_id', 'int'),),
                 Events.on_socket_raw_receive: (('msg', 'Union[bytes, str]'),),
                 Events.on_socket_raw_send: (('payload', 'Union[bytes, str]'),),
                 Events.on_typing: (('channel', 'abc.Messageable'), ('user', 'Union[discord.User, discord.Member]'), ('when', 'datetime')),
                 Events.on_message: (('message', 'discord.Message'),),
                 Events.on_message_delete: (('message', 'discord.Message'),),
                 Events.on_bulk_message_delete: (('messages', 'List[discord.Message]'),),
                 Events.on_raw_message_delete: (('payload', 'discord.RawMessageDeleteEvent'),),
                 Events.on_raw_bulk_message_delete: (('payload', 'discord.RawMessageDeleteEvent'),),
                 Events.on_message_edit: (('before', 'discord.Message'), ('after', 'discord.Message')),
                 Events.on_raw_message_edit: (('payload', 'discord.RawMessageUpdateEvent'),),
                 Events.on_reaction_add: (('reaction', 'discord.Reaction'), ('user', 'Union[discord.User, discord.Member]')),
                 Events.on_raw_reaction_add: (('payload', 'discord.RawReactionActionEvent'),),
                 Events.on_reaction_remove: (('reaction', 'discord.Reaction'), ('user', 'Union[discord.User, discord.Member]')),
                 Events.on_raw_reaction_remove: (('payload', 'discord.RawReactionActionEvent'),),
                 Events.on_reaction_clear: (('message', 'discord.Message'), ('reactions', 'List[discord.Reaction]')),
                 Events.on_raw_reaction_clear: (('payload', 'discord.RawReactionClearEvent'),),
                 Events.on_reaction_clear_emoji: (('reaction', 'discord.Reaction'),),
                 Events.on_raw_reaction_clear_emoji: (('payload', 'discord.RawReactionClearEmojiEvent'),),
                 Events.on_private_channel_delete: (('channel', 'discord.abc.PrivateChannel'),),
                 Events.on_private_channel_create: (('channel', 'discord.abc.PrivateChannel'),),
                 Events.on_private_channel_update: (('before', 'discord.GroupChannel'), ('after', 'discord.GroupChannel')),
                 Events.on_private_channel_pins_update: (('channel', 'discord.GroupChannel'), ('last_pin', 'datetime')),
                 Events.on_guild_channel_delete: (('channel', 'discord.abc.GuildChannel'),),
                 Events.on_guild_channel_create: (('channel', 'discord.abc.GuildChannel'),),
                 Events.on_guild_channel_update: (('before', 'discord.abc.GuildChannel'), ('after', 'discord.abc.GuildChannel')),
                 Events.on_guild_channel_pins_update: (('channel', 'discord.abc.GuildChannel'), ('last_pin', 'datetime')),
                 Events.on_guild_integrations_update: (('guild', 'discord.Guild'),),
                 Events.on_webhooks_update: (('channel', 'discord.abc.GuildChannel'),),
                 Events.on_member_join: (('member', 'discord.Member'),),
                 Events.on_member_remove: (('member', 'discord.Member'),),
                 Events.on_member_update: (('before', 'discord.Member'), ('after', 'discord.Member')),
                 Events.on_user_update: (('before', 'discord.User'), ('after', 'discord.User')),
                 Events.on_guild_join: (('guild', 'discord.Guild'),),
                 Events.on_guild_remove: (('guild', 'discord.Guild'),),
                 Events.on_guild_update: (('guild', 'discord.Guild'), ('guild', 'discord.Guild')),
                 Events.on_guild_role_create: (('role', 'discord.Role'),),
                 Events.on_guild_role_delete: (('role', 'discord.Role'),),
                 Events.on_guild_role_update: (('role', 'discord.Role'), ('role', 'discord.Role')),
                 Events.on_guild_emojis_update: (('guild', 'discord.Guild'), ('before', 'Sequence[discord.Emoji]'), ('after', 'Sequence[discord.Emoji]')),
                 Events.on_guild_available: (('guild', 'discord.Guild'),),
                 Events.on_guild_unavailable: (('guild', 'discord.Guild'),),
                 Events.on_voice_state_update: (('member', 'discord.Member'), ('before', 'discord.VoiceState'), ('after', 'discord.VoiceState')),
                 Events.on_member_ban: (('guild', 'discord.Guild'), ('user', 'Union[discord.User,discord.Member]')),
                 Events.on_member_unban: (('guild', 'discord.Guild'), ('user', 'discord.User')),
                 Events.on_invite_create: (('invite', 'discord.Invite'),),
                 Events.on_invite_delete: (('invite', 'discord.Invite'),),
                 Events.on_group_join: (('channel', 'discord.GroupChannel'), ('user', 'discord.User')),
                 Events.on_group_remove: (('channel', 'discord.GroupChannel'), ('user', 'discord.User')),
                 Events.on_relationship_add: (('relationship', 'discord.Relationship'),),
                 Events.on_relationship_remove: (('relationship', 'discord.Relationship'),),
                 Events.on_relationship_update: (('before', 'discord.Relationship'), ('after', 'discord.Relationship'))}
