"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
from datetime import datetime
from typing import TYPE_CHECKING, Union, Callable, Iterable, List, Tuple, Set
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands import Converter, CommandError
from googletrans import LANGUAGES
from discord.ext import commands, tasks, flags
import discord
from dateparser import parse as date_parse
from validator_collection import validators
import validator_collection
from enum import Enum, auto, Flag
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from antipetros_discordbot.utility.exceptions import ParameterError, ParameterErrorWithPossibleParameter
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCommand, AntiPetrosBaseGroup, AntiPetrosFlagCommand, CommandCategory
from antipetros_discordbot.engine.replacements import CommandCategory
from antipetros_discordbot.utility.checks import (OnlyGiddiCheck, OnlyBobMurphyCheck, BaseAntiPetrosCheck, AdminOrAdminLeadCheck, AllowedChannelAndAllowedRoleCheck,
                                                  HasAttachmentCheck, OnlyGiddiCheck, OnlyBobMurphyCheck)
from antipetros_discordbot.utility.misc import check_if_url, fix_url_prefix
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import ExtraHelpParameter, HelpCategory
from icecream import ic
if TYPE_CHECKING:
    pass

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
        ic(argument)

        command = bot.command_dict.get(argument)
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


        # region[Main_Exec]
if __name__ == '__main__':
    pass


# endregion[Main_Exec]
