# * Third Party Imports -->
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands.errors import CommandError
from datetime import datetime
from typing import Any


class AntiPetrosBaseError(Exception):
    pass


class ClassAttributesNotSetError(AntiPetrosBaseError):
    def __init__(self, missing_attr_name: str):
        self.missing_attr = missing_attr_name
        self.msg = f"mandatory class attribute '{self.missing_attr}' is None"
        super().__init__(self.msg)


class FaqParseError(AntiPetrosBaseError):
    pass


class FaqNumberParseError(FaqParseError):
    def __init__(self, raw_content: str, jump_url: str) -> None:
        self.raw_content = raw_content
        self.url = jump_url
        self.msg = f"unable to parse number from FAQ '{self.url}'"
        super().__init__(self.msg)


class FaqQuestionParseError(FaqParseError):
    def __init__(self, raw_content: str, jump_url: str) -> None:
        self.raw_content = raw_content
        self.url = jump_url
        self.msg = f"unable to parse question from FAQ '{self.url}'"
        super().__init__(self.msg)


class TeamMemberRoleNotFoundError(AntiPetrosBaseError):
    def __init__(self, team_name: str) -> None:
        self.team_name = team_name
        self.msg = f"No Member Role found for Team {self.team_name}"
        super().__init__(self.msg)


class FaqAnswerParseError(FaqParseError):
    def __init__(self, raw_content: str, jump_url: str) -> None:
        self.raw_content = raw_content
        self.url = jump_url
        self.msg = f"unable to parse answer from FAQ '{self.url}'"
        super().__init__(self.msg)


class NeededConfigValueMissing(AntiPetrosBaseError):
    def __init__(self, option_name, section_name, class_name) -> None:
        self.option_name = option_name
        self.section_name = section_name
        self.class_name = class_name
        self.msg = f"The option '{self.option_name}' was not set in section '{self.section_name}' and is needed for the class '{self.class_name}'"
        super().__init__(self.msg)


class NeededClassAttributeNotSet(AntiPetrosBaseError):
    def __init__(self, attr_name: str, class_name: str):
        self.attr_name = attr_name
        self.class_name = class_name
        self.msg = f"The class attribute '{self.attr_name}' was not set in the class '{self.class_name}'!"
        super().__init__(self.msg)


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


class TokenMissingError(TokenError):
    def __init__(self, token_name):
        self.token_name = token_name
        self.msg = f"Token '{self.token_name}' is not set as env variable!"
        super().__init__(self.msg)


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
        self.msg = f"Sorry {ctx.author.name} I can't let you do that.\n\nThe command '{self.command_name}' (alias used: '{self.alias_used}') is not allowed in channel '{self.channel_name}'"
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


class NotAllowedMember(BaseExtendedCommandError):
    def __init__(self, allowed_member_ids: list):
        self.allowed_member_ids = allowed_member_ids
        self.msg = "You are not in the list of members that are allowed to use this command"
        super().__init__(self.msg)


class ParameterError(BaseExtendedCommandError):
    def __init__(self, parameter_name: str = None, parameter_value=None, error=None) -> None:
        self.name = parameter_name
        self.value = parameter_value
        self._error = error
        self.msg = f"'{self.value}' is not a valid input"
        if self.name is not None:
            self.msg += f" for '{self.name}'"
        super().__init__(self.msg)

    @property
    def error(self):
        if self._error is None:
            return self
        return self._error


class ParameterErrorWithPossibleParameter(BaseExtendedCommandError):
    def __init__(self, parameter_name: str, parameter_value, possible_parameter: list):
        self.name = parameter_name
        self.value = parameter_value
        self.possible_parameter = possible_parameter
        self.msg = f"'{self.value}' is not a valid input for '{self.name}'\nPossible values are:\n" + "\n".join(f"\t`{item}`" for item in self.possible_parameter)
        super().__init__(self.msg)


class ParseDiceLineError(BaseExtendedCommandError):
    def __init__(self, statement) -> None:
        self.statement = statement
        self.msg = f"Unable to parse dice input '{self.statement}'"
        super().__init__(self.msg)


class CustomEmojiError(BaseExtendedCommandError):
    def __init__(self, custom_emoji_name: str, problem: str):
        self.custom_emoji_name = custom_emoji_name
        self.problem = problem
        self.msg = f"Error with custom emoji '{self.custom_emoji_name}': {self.problem}"
        super().__init__(self.msg)


class NameInUseError(BaseExtendedCommandError):
    def __init__(self, name: str, typus: str):
        self.name = name
        self.typus = typus
        self.msg = f"The Name {self.name} is already in use for {self.typus} items"
        super().__init__(self.msg)


class GithubRateLimitUsedUp(BaseExtendedCommandError):
    def __init__(self, reset_time: datetime):
        self.reset_time = reset_time
        self.msg = "Rate Limit for github is used up, this action is not usable until " + self.reset_time.strftime("%Y-%m-%d %H:%M:%S UTC") + ", as the rate-limit resets at that time!"
        super().__init__(self.msg)
