from discord.ext.commands.errors import CommandError


class AntiPetrosBaseError(Exception):
    pass


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
        self.msg = f"This command requires at least {str(self.min_attachments)} attachments to work\nAmount attachments provided: {str(len(self.attachments))}."
        super().__init__(self.msg)


class NotAllowedChannelError(BaseExtendedCommandError):
    def __init__(self, ctx, allowed_channels):
        self.ctx = ctx
        self.command_name = ctx.command
        self.channel_name = self.ctx.channel.name
        self.allowed_channels = allowed_channels
        self.msg = f"The command '{self.command_name}' is not allowed in channel '{self.channel_name}'"
        super().__init__(self.msg)


class NotNecessaryRole(BaseExtendedCommandError):
    def __init__(self, ctx, allowed_roles):
        self.ctx = ctx
        self.allowed_roles = allowed_roles
        self.msg = "You do not have the necessary Role to invoke this command"
        super().__init__(self.msg)


class IsNotTextChannelError(BaseExtendedCommandError):
    def __init__(self, ctx, channel_type):
        self.ctx = ctx
        self.command = self.ctx.command
        self.channel_type = channel_type
        self.msg = f"The command '{self.command.name}' is not allowed in DM's"
        super().__init__(self.msg)
