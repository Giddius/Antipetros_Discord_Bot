# * Third Party Imports -->
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands.errors import CommandError


class AntiPetrosBaseError(Exception):
    pass


class MissingNeededAttributeError(AntiPetrosBaseError):
    def __init__(self, attr_name, cog) -> None:
        self.cog = cog
        self.attr_name = attr_name
        self.msg = f"Cog '{self.cog.qualified_name}' is missing the needed attribute '{self.attr_name}'"
        super().__init__(self.msg)


class CogNameNotCamelCaseError(AntiPetrosBaseError):
    pass


class FuzzyMatchError(AntiPetrosBaseError):
    def __init__(self, query, scorer, limit=None, data=None):
        self.query = query
        self.data = data
        self.scorer = scorer
        self.scorer_name = str(self.scorer).replace("<function ", "").split(' ')[0] if str(self.scorer).startswith('<') else str(self.scorer)
        self.limit = limit
        self.msg = f"Unable to fuzzy find a match for '{self.query}' with scorer '{self.scorer_name}'"
        if self.limit is not None:
            self.msg += f" and a limit of '{self.limit}'"
        super().__init__(self.msg)


class TokenError(AntiPetrosBaseError):
    __module__ = 'antipetros-discordbot'


class DuplicateNameError(AntiPetrosBaseError):
    def __init__(self, name, container_name):
        self.msg = f"Name '{name}' is already in '{container_name}' and it does not allow duplicates."
        super().__init__(self.msg)


class BaseExtendedCommandError(CommandError):
    pass


class MissingAttachmentError(BaseExtendedCommandError):

    def __init__(self, ctx, min_attachments: int):
        self.ctx = ctx
        self.command = self.ctx.command
        self.min_attachments = min_attachments
        self.attachments = self.ctx.message.attachments
        self.msg = f"This command requires at least '{str(self.min_attachments)}' attachments to work\nAmount attachments provided: '{str(len(self.attachments))}'."
        super().__init__(self.msg)


class NotAllowedChannelError(BaseExtendedCommandError):
    def __init__(self, ctx, allowed_channels):
        self.ctx = ctx
        self.command_name = ctx.command
        self.alias_used = ctx.invoked_with
        self.channel_name = self.ctx.channel.name
        self.allowed_channels = allowed_channels
        self.msg = f"The command '{self.command_name}' (alias used: '{self.alias_used}') is not allowed in channel '{self.channel_name}'"
        super().__init__(self.msg)


class NotNecessaryRole(BaseExtendedCommandError):
    def __init__(self, ctx, allowed_roles):
        self.ctx = ctx
        self.allowed_roles = allowed_roles
        self.command_name = self.ctx.command
        self.alias_used = self.ctx.invoked_with
        self.channel_name = self.ctx.channel.name
        self.msg = f"You do not have the necessary Role to invoke the command '{self.command_name}' (alias used: '{self.alias_used}')"
        super().__init__(self.msg)


class IsNotTextChannelError(BaseExtendedCommandError):
    def __init__(self, ctx, channel_type):
        self.ctx = ctx
        self.command = self.ctx.command
        self.channel_type = channel_type
        self.msg = f"The command '{self.command.name}' is not allowed in DM's"
        super().__init__(self.msg)


class IsNotDMChannelError(BaseExtendedCommandError):
    def __init__(self, ctx, channel_type):
        self.ctx = ctx
        self.command = self.ctx.command
        self.channel_type = channel_type
        self.msg = f"The command '{self.command.name}' is not allowed outside of DM's"
        super().__init__(self.msg)


class NotNecessaryDmId(BaseExtendedCommandError):
    def __init__(self, ctx):
        self.ctx = ctx
        self.command_name = ctx.command
        self.alias_used = ctx.invoked_with
        self.msg = f"You do not have the necessary Permission to invoke the Dm command '{self.command_name}' (alias used: '{self.alias_used}')!"
        super().__init__(self.msg)
