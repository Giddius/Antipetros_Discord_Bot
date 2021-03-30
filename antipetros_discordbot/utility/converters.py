"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
from datetime import datetime

# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext.commands import Converter, CommandError
from googletrans import LANGUAGES
from discord.ext import commands, tasks, flags
import discord
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
from antipetros_discordbot.utility.exceptions import ParameterError
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

    async def convert(self, ctx: commands.Context, argument):
        bot = ctx.bot
        command = await bot.command_by_name(argument)
        if command is None:
            raise ParameterError('command', argument)
        return command


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
