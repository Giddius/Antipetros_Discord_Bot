# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum

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


class ListenerEvents(Enum):
    on_connect = 'on_connect'
    on_shard_connect = 'on_shard_connect'
    on_disconnect = 'on_disconnect'
    on_shard_disconnect = 'on_shard_disconnect'
    on_ready = 'on_ready'
    on_shard_ready = 'on_shard_ready'
    on_resumed = 'on_resumed'
    on_shard_resumed = 'on_shard_resumed'
    on_socket_raw_receive = 'on_socket_raw_receive'
    on_socket_raw_send = 'on_socket_raw_send'
    on_typing = 'on_typing'
    on_message = 'on_message'
    on_message_delete = 'on_message_delete'
    on_bulk_message_delete = 'on_bulk_message_delete'
    on_raw_message_delete = 'on_raw_message_delete'
    on_raw_bulk_message_delete = 'on_raw_bulk_message_delete'
    on_message_edit = 'on_message_edit'
    on_raw_message_edit = 'on_raw_message_edit'
    on_reaction_add = 'on_reaction_add'
    on_raw_reaction_add = 'on_raw_reaction_add'
    on_reaction_remove = 'on_reaction_remove'
    on_raw_reaction_remove = 'on_raw_reaction_remove'
    on_reaction_clear = 'on_reaction_clear'
    on_raw_reaction_clear = 'on_raw_reaction_clear'
    on_reaction_clear_emoji = 'on_reaction_clear_emoji'
    on_raw_reaction_clear_emoji = 'on_raw_reaction_clear_emoji'
    on_private_channel_delete = 'on_private_channel_delete'
    on_private_channel_create = 'on_private_channel_create'
    on_private_channel_update = 'on_private_channel_update'
    on_private_channel_pins_update = 'on_private_channel_pins_update'
    on_guild_channel_delete = 'on_guild_channel_delete'
    on_guild_channel_create = 'on_guild_channel_create'
    on_guild_channel_update = 'on_guild_channel_update'
    on_guild_channel_pins_update = 'on_guild_channel_pins_update'
    on_guild_integrations_update = 'on_guild_integrations_update'
    on_webhooks_update = 'on_webhooks_update'
    on_member_join = 'on_member_join'
    on_member_remove = 'on_member_remove'
    on_member_update = 'on_member_update'
    on_user_update = 'on_user_update'
    on_guild_join = 'on_guild_join'
    on_guild_remove = 'on_guild_remove'
    on_guild_update = 'on_guild_update'
    on_guild_role_create = 'on_guild_role_create'
    on_guild_role_delete = 'on_guild_role_delete'
    on_guild_role_update = 'on_guild_role_update'
    on_guild_emojis_update = 'on_guild_emojis_update'
    on_guild_available = 'on_guild_available'
    on_guild_unavailable = 'on_guild_unavailable'
    on_voice_state_update = 'on_voice_state_update'
    on_member_ban = 'on_member_ban'
    on_member_unban = 'on_member_unban'
    on_invite_create = 'on_invite_create'
    on_invite_delete = 'on_invite_delete'
    on_group_join = 'on_group_join'
    on_group_remove = 'on_group_remove'
    on_relationship_add = 'on_relationship_add'
    on_relationship_remove = 'on_relationship_remove'
    on_relationship_update = 'on_relationship_update'

    def __str__(self):
        return str(self.name)

    @classmethod
    def get_event_parameter_mapping(cls):
        return {cls.on_connect: (),
                cls.on_shard_connect: (('shard_id', 'int'),),
                cls.on_disconnect: (),
                cls.on_shard_disconnect: (('shard_id', 'int'),),
                cls.on_ready: (),
                cls.on_shard_ready: (('shard_id', 'int'),),
                cls.on_resumed: (),
                cls.on_shard_resumed: (('shard_id', 'int'),),
                cls.on_socket_raw_receive: (('msg', 'Union[bytes, str]'),),
                cls.on_socket_raw_send: (('payload', 'Union[bytes, str]'),),
                cls.on_typing: (('channel', 'abc.Messageable'), ('user', 'Union[discord.User, discord.Member]'), ('when', 'datetime')),
                cls.on_message: (('message', 'discord.Message'),),
                cls.on_message_delete: (('message', 'discord.Message'),),
                cls.on_bulk_message_delete: (('messages', 'List[discord.Message]'),),
                cls.on_raw_message_delete: (('payload', 'discord.RawMessageDeleteEvent'),),
                cls.on_raw_bulk_message_delete: (('payload', 'discord.RawMessageDeleteEvent'),),
                cls.on_message_edit: (('before', 'discord.Message'), ('after', 'discord.Message')),
                cls.on_raw_message_edit: (('payload', 'discord.RawMessageUpdateEvent'),),
                cls.on_reaction_add: (('reaction', 'discord.Reaction'), ('user', 'Union[discord.User, discord.Member]')),
                cls.on_raw_reaction_add: (('payload', 'discord.RawReactionActionEvent'),),
                cls.on_reaction_remove: (('reaction', 'discord.Reaction'), ('user', 'Union[discord.User, discord.Member]')),
                cls.on_raw_reaction_remove: (('payload', 'discord.RawReactionActionEvent'),),
                cls.on_reaction_clear: (('message', 'discord.Message'), ('reactions', 'List[discord.Reaction]')),
                cls.on_raw_reaction_clear: (('payload', 'discord.RawReactionClearEvent'),),
                cls.on_reaction_clear_emoji: (('reaction', 'discord.Reaction'),),
                cls.on_raw_reaction_clear_emoji: (('payload', 'discord.RawReactionClearEmojiEvent'),),
                cls.on_private_channel_delete: (('channel', 'discord.abc.PrivateChannel'),),
                cls.on_private_channel_create: (('channel', 'discord.abc.PrivateChannel'),),
                cls.on_private_channel_update: (('before', 'discord.GroupChannel'), ('after', 'discord.GroupChannel')),
                cls.on_private_channel_pins_update: (('channel', 'discord.GroupChannel'), ('last_pin', 'datetime')),
                cls.on_guild_channel_delete: (('channel', 'discord.abc.GuildChannel'),),
                cls.on_guild_channel_create: (('channel', 'discord.abc.GuildChannel'),),
                cls.on_guild_channel_update: (('before', 'discord.abc.GuildChannel'), ('after', 'discord.abc.GuildChannel')),
                cls.on_guild_channel_pins_update: (('channel', 'discord.abc.GuildChannel'), ('last_pin', 'datetime')),
                cls.on_guild_integrations_update: (('guild', 'discord.Guild'),),
                cls.on_webhooks_update: (('channel', 'discord.abc.GuildChannel'),),
                cls.on_member_join: (('member', 'discord.Member'),),
                cls.on_member_remove: (('member', 'discord.Member'),),
                cls.on_member_update: (('before', 'discord.Member'), ('after', 'discord.Member')),
                cls.on_user_update: (('before', 'discord.User'), ('after', 'discord.User')),
                cls.on_guild_join: (('guild', 'discord.Guild'),),
                cls.on_guild_remove: (('guild', 'discord.Guild'),),
                cls.on_guild_update: (('guild', 'discord.Guild'), ('guild', 'discord.Guild')),
                cls.on_guild_role_create: (('role', 'discord.Role'),),
                cls.on_guild_role_delete: (('role', 'discord.Role'),),
                cls.on_guild_role_update: (('role', 'discord.Role'), ('role', 'discord.Role')),
                cls.on_guild_emojis_update: (('guild', 'discord.Guild'), ('before', 'Sequence[discord.Emoji]'), ('after', 'Sequence[discord.Emoji]')),
                cls.on_guild_available: (('guild', 'discord.Guild'),),
                cls.on_guild_unavailable: (('guild', 'discord.Guild'),),
                cls.on_voice_state_update: (('member', 'discord.Member'), ('before', 'discord.VoiceState'), ('after', 'discord.VoiceState')),
                cls.on_member_ban: (('guild', 'discord.Guild'), ('user', 'Union[discord.User,discord.Member]')),
                cls.on_member_unban: (('guild', 'discord.Guild'), ('user', 'discord.User')),
                cls.on_invite_create: (('invite', 'discord.Invite'),),
                cls.on_invite_delete: (('invite', 'discord.Invite'),),
                cls.on_group_join: (('channel', 'discord.GroupChannel'), ('user', 'discord.User')),
                cls.on_group_remove: (('channel', 'discord.GroupChannel'), ('user', 'discord.User')),
                cls.on_relationship_add: (('relationship', 'discord.Relationship'),),
                cls.on_relationship_remove: (('relationship', 'discord.Relationship'),),
                cls.on_relationship_update: (('before', 'discord.Relationship'), ('after', 'discord.Relationship'))}
