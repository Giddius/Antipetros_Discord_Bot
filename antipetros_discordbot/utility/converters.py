"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
from datetime import datetime
from collections import defaultdict
from typing import Callable, TYPE_CHECKING, Union
import inspect
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands import Converter, CommandError
from googletrans import LANGUAGES
from discord.ext import commands, tasks, flags
import discord
from dateparser import parse as date_parse
from validator_collection import validators
import validator_collection
from enum import Enum
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from antipetros_discordbot.utility.exceptions import ParameterError, ParameterErrorWithPossibleParameter
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand, CommandCategory
from antipetros_discordbot.engine.replacements import CommandCategory
from antipetros_discordbot.utility.checks import (OnlyGiddiCheck, OnlyBobMurphyCheck, BaseAntiPetrosCheck, AdminOrAdminLeadCheck, AllowedChannelAndAllowedRoleCheck,
                                                  HasAttachmentCheck, OnlyGiddiCheck, OnlyBobMurphyCheck)
from antipetros_discordbot.utility.misc import check_if_url, fix_url_prefix
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import ExtraHelpParameter, HelpCategory, GithubLabelOperator
from functools import partial
if TYPE_CHECKING:
    pass
import asyncio
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
log.info(glog.imported(__name__))

# endregion[Logging]

# region [Constants]
APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class LanguageConverter(Converter):
    def __init__(self):
        self.languages = {value.casefold(): key for key, value in LANGUAGES.items()}
        self.languages_by_country_code = {key.casefold(): key for key in LANGUAGES}

    async def convert(self, ctx, argument):
        argument = argument.casefold()
        if argument in self.languages:
            return self.languages.get(argument)
        elif argument in self.languages_by_country_code:
            return self.languages_by_country_code.get(argument)
        raise CommandError

    @classmethod
    @property
    def usage_description(cls):
        return "Name of the language or language code (iso639-1). Case-INsensitive"


class DateTimeFullConverter(Converter):
    def __init__(self):
        self.format = "%Y-%m-%d_%H-%M-%S"
        self.date_and_time_regex = re.compile(r'(?P<year>\d\d\d\d).*?(?P<month>[01]\d).*?(?P<day>[0123]\d).*?(?P<hour>[012]\d).*?(?P<minute>[0-6]\d).*?(?P<second>[0-6]\d)')

    async def convert(self, ctx, argument):
        result = self.date_and_time_regex.search(argument)
        if result is None:
            raise CommandError("wrong date and time format")
        result_dict = result.groupdict()
        new_argument = f"{result_dict.get('year')}-{result_dict.get('month')}-{result_dict.get('day')}_{result_dict.get('hour')}-{result_dict.get('minute')}-{result_dict.get('second')}"
        try:
            return datetime.strptime(new_argument, self.format)
        except Exception as error:
            raise CommandError(error)


class DateOnlyConverter(Converter):
    def __init__(self):
        self.format = "%Y-%m-%d"
        self.date_regex = re.compile(r'(?P<year>\d\d\d\d).*?(?P<month>[01]\d).*?(?P<day>[0123]\d)')

    async def convert(self, ctx, argument):
        result = self.date_regex.search(argument)
        if result is None:
            raise CommandError("wrong date and time format")
        result_dict = result.groupdict()
        new_argument = f"{result_dict.get('year')}-{result_dict.get('month')}-{result_dict.get('day')}"
        try:
            return datetime.strptime(new_argument, self.format)
        except Exception as error:
            raise CommandError(error)


class FlagArg(Converter):
    def __init__(self, available_flags):
        self.available_flags = available_flags

    async def convert(self, ctx, argument):
        if argument.startswith('--'):
            name = argument.removeprefix('--').replace('-', '_').lower()
            if name in self.available_flags:
                return name
            else:
                raise CommandError
        else:
            raise CommandError


class CommandConverter(Converter):

    async def convert(self, ctx: commands.Context, argument) -> Union[commands.Command, AntiPetrosBaseCommand, AntiPetrosFlagCommand, AntiPetrosBaseGroup]:
        bot = ctx.bot

        command = bot.commands_map.get(argument)
        if command is None:
            raise ParameterError('command', argument)
        return command

    @classmethod
    @property
    def usage_description(cls):
        return "The name or alias of a Command that this bot has. Case-INsensitive"


def date_time_full_converter_flags(argument):
    return date_parse(argument)


class CogConverter(Converter):

    async def convert(self, ctx: commands.Context, argument):
        bot = ctx.bot
        mod_argument = argument.casefold()
        if not mod_argument.endswith('cog'):
            mod_argument += 'cog'

        cog = await bot.get_cog(mod_argument)
        if cog is None:
            raise ParameterError("cog", argument)
        return cog

    @classmethod
    @property
    def usage_description(cls):
        return "The name of a Cog that this bot has. Case-INsensitive"


class CategoryConverter(Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> CommandCategory:
        try:
            norm_name = await self._normalize_argument(argument)
            _out = getattr(CommandCategory, norm_name)
            return _out
        except (TypeError, ValueError) as e:
            raise ParameterError("category", argument) from e

    async def _normalize_argument(self, argument: str):
        if argument is not None:
            argument = argument.replace('_', '').replace(' ', '')
            argument = argument.casefold()
            return argument.removesuffix('commandcategory').upper()

    @classmethod
    @property
    def usage_description(cls):
        return "The name of a Command-Category this bot has. Case-INsensitive\nPossible Values: " + '\n'.join(item for item in CommandCategory.all_command_categories)


class CheckConverter(Converter):
    check_map = {'adminoradminleadcheck': AdminOrAdminLeadCheck,
                 'allowed_channel_and_allowed_role': AllowedChannelAndAllowedRoleCheck,
                 'allowedchannelandallowedrolecheck': AllowedChannelAndAllowedRoleCheck,
                 'baseantipetroscheck': BaseAntiPetrosCheck,
                 'has_attachments': HasAttachmentCheck,
                 'hasattachmentcheck': HasAttachmentCheck,
                 'only_bob': OnlyBobMurphyCheck,
                 'onlybobmurphycheck': OnlyBobMurphyCheck,
                 'only_giddi': OnlyGiddiCheck,
                 'onlygiddicheck': OnlyGiddiCheck,
                 'owner_or_admin': AdminOrAdminLeadCheck}

    async def convert(self, ctx: commands.Context, argument) -> Callable:
        _out = self.check_map.get(argument.casefold(), None)
        if _out is None:
            raise ParameterError("check", argument)
        return _out

    @classmethod
    @property
    def usage_description(cls):
        return "The name of a Command-Check-Function this bot has. Case-INsensitive\nPossible Values: " + '\n'.join(item for item in cls.check_map)


class UrlConverter(Converter):

    async def convert(self, ctx: commands.Context, argument) -> str:
        if await check_if_url(argument) is False:
            raise ParameterError("url", argument)

        return fix_url_prefix(argument)

    @classmethod
    @property
    def usage_description(cls):
        return "A valid URL"


class HelpCategoryConverter(Converter):
    possible_parameter_enum = HelpCategory

    async def convert(self, ctx: commands.Context, argument):
        mod_argument = await self._normalize_argument(argument)
        try:
            _out = self.possible_parameter_enum(mod_argument)
        except ValueError:
            raise ParameterErrorWithPossibleParameter('help_catgories', argument, list(self.possible_parameter_enum.__members__))

        return _out

    async def _normalize_argument(self, argument: str):
        mod_argument = argument.casefold()
        return mod_argument.replace(' ', '').replace('-', '')

    @classmethod
    @property
    def usage_description(cls):
        return "Name of a Help-Category. Case-INsensitive.\nPossible Values: " + '\n'.join(name for name in HelpCategory.__members__)


class ExtraHelpParameterConverter(Converter):
    possible_parameter_enum = ExtraHelpParameter

    async def convert(self, ctx: commands.Context, argument) -> Enum:
        mod_argument = await self._normalize_argument(argument)
        try:
            _out = self.possible_parameter_enum(mod_argument)
        except ValueError:
            raise ParameterErrorWithPossibleParameter('extra_help_parameter', argument, list(self.possible_parameter_enum.__members__))
        return _out

    async def _normalize_argument(self, argument: str):
        mod_argument = argument.casefold()
        return mod_argument.replace(' ', '').replace('_', '').replace('-', '')

    @classmethod
    @property
    def usage_description(cls):
        return "Name of an Extra-Help-Parameter. Case-INsensitive.\nPossible Values: " + '\n'.join(name for name in ExtraHelpParameter.__members__)


class RoleOrIntConverter(Converter):

    async def convert(self, ctx: commands.Context, argument):
        if argument.isnumeric() is False or len(str(argument)) == 18:
            log.debug('argument "%s" is not an pure integer', argument)
            return await self.convert_to_role(ctx, argument)

        return int(argument)

    async def convert_to_role(self, ctx: commands.Context, argument):
        if argument.isnumeric():
            role = ctx.bot.get_antistasi_role(int(argument))
        else:
            role = ctx.bot.role_from_string(argument)
        if role is None:
            raise ParameterError("role", argument)
        return role


class SeparatedListConverter(Converter):

    def __init__(self, value_type: Union[Callable, Converter] = str, separator: str = ',', strip_whitespace: bool = True):
        self.value_type = value_type
        self.separator = separator
        self.strip_whitespace = strip_whitespace

    async def get_parameter_name(self, ctx: commands.Context):
        command = ctx.command
        for param_name, param in command.clean_params.items():
            if param.annotation is self:
                return param_name
            await asyncio.sleep(0)

    async def convert(self, ctx: commands.Context, argument):
        parts = argument.split(self.separator)
        if self.strip_whitespace is True:
            parts = list(map(lambda x: x.strip(), parts))
        parts = [part for part in parts if part != '']
        if parts == []:
            raise ParameterError(parameter_name=await self.get_parameter_name(ctx), parameter_value=argument)

        try:
            if inspect.isclass(self.value_type) and issubclass(self.value_type, Converter):
                instance = self.value_type()
                return [await instance.convert(ctx, part) for part in parts]
            if hasattr(self.value_type, 'convert'):
                return [await self.value_type.convert(ctx, part) for part in parts]
            else:
                return list(map(self.value_type, parts))
        except Exception as error:
            if not isinstance(error, CommandError):
                log.error(error, exc_info=True)
                raise ParameterError(parameter_name=await self.get_parameter_name(ctx), parameter_value=argument, error=error)
            else:
                raise error


class GitHubLabelConverter(Converter):
    _possible_params = None

    @classmethod
    async def get_possible_params(cls, default_labels):
        if cls._possible_params is None:
            cls._possible_params = [label.name for label in default_labels.values()]

        return cls._possible_params

    async def convert(self, ctx: commands.Context, argument: str):
        _out = []

        labels = ctx.cog.labels
        for in_label in argument.split(';'):
            in_label = in_label.strip()
            if in_label != '' and in_label.casefold() in set(labels):
                _out.append(labels.get(in_label.casefold()))

        return _out


class GithubLabelOperatorConverter(Converter):
    operator_mapping = {'+': GithubLabelOperator.AND,
                        'and': GithubLabelOperator.AND,
                        '=': GithubLabelOperator.AND,
                        '==': GithubLabelOperator.AND,
                        '~': GithubLabelOperator.OR,
                        '*': GithubLabelOperator.OR,
                        '|': GithubLabelOperator.OR,
                        'or': GithubLabelOperator.OR,
                        '-': GithubLabelOperator.NOT,
                        'not': GithubLabelOperator.NOT,
                        '!': GithubLabelOperator.NOT,
                        '!=': GithubLabelOperator.NOT,
                        'notany': GithubLabelOperator.NOT_ANY,
                        '!*': GithubLabelOperator.NOT_ANY}

    _possible_params = None

    @classmethod
    async def get_possible_params(cls):
        if cls._possible_params is None:
            possible_params_dict = defaultdict(list)
            for key, value in cls.operator_mapping.items():
                possible_params_dict[value.name].append(key)

            cls._possible_params = [f"{key} -> {', '.join(value)}" for key, value in possible_params_dict.items()]
        return cls._possible_params

    async def convert(self, ctx: commands.Context, argument: str):
        if argument.casefold() not in self.operator_mapping:
            raise ParameterErrorWithPossibleParameter('label_operator', argument, await self.get_possible_params())
        query_argument = argument.casefold().replace('-', '').replace('_', '') if argument != '-' and argument != '_' else argument.casefold()
        return self.operator_mapping.get(query_argument)


# region[Main_Exec]
if __name__ == '__main__':
    pass


# endregion[Main_Exec]
