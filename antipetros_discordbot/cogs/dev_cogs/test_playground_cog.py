# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
import subprocess
from io import StringIO
from pprint import pformat
from datetime import datetime
from tempfile import TemporaryDirectory
from functools import partial

# * Third Party Imports --------------------------------------------------------------------------------->

import discord
from pytz import timezone
from discord.ext import commands
from googletrans import LANGUAGES, Translator
from discord.ext.commands import Greedy
from antistasi_template_checker.engine.antistasi_template_parser import run as template_checker_run

# * Gid Imports ----------------------------------------------------------------------------------------->

import gidlogger as glog

# * Local Imports --------------------------------------------------------------------------------------->

from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.checks import log_invoker, has_attachments, in_allowed_channels
from antipetros_discordbot.utility.converters import FlagArg, DateOnlyConverter
from antipetros_discordbot.utility.gidtools_functions import loadjson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.enums import CogState
# endregion [Imports]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]


APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

HELP_TEST_DATA = loadjson(APPDATA["command_help.json"])
CONFIG_NAME = "test_playground"

FAQ_THING = """**FAQ No 17**
_How to become a server member?_
_Read the channel description on teamspeak or below_

_**Becoming a member:**_
```
Joining our ranks is simple: play with us and participate in this community! If the members like you you may be granted trial membership by an admin upon recommendation.

Your contribution and participation to this community will determine how long the trial period will be, and whether or not it results in full membership. As a trial member, you will receive in-game membership and a [trial] tag on these forums which assures you an invite to all events including official member meetings. Do note that only full members are entitled to vote on issues at meetings.
```"""


class TestPlaygroundCog(commands.Cog, command_attrs={'hidden': True, "name": "TestPlayground"}):
    """
    Soon
    """
    config_name = "test_playground"
    language_dict = {value: key for key, value in LANGUAGES.items()}
    docattrs = {'show_in_readme': False,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.OUTDATED | CogState.CRASHING | CogState.DOCUMENTATION_MISSING | CogState.FOR_DEBUG,
                             "2021-02-06 05:27:52",
                             "206141b64e3688eedda4d196dada700bdff9a22170c5557515d8cfd99706d56e42771c27e121dfddbbfb093a1edcdf7bde66fada427201e47ef72a40d7b4f2b1")}

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = set(COGS_CONFIG.getlist('test_playground', 'allowed_channels'))
        self.translator = Translator()
        glog.class_init_notification(log, self)

    @commands.command(aliases=get_aliases("check_date_converter"))
    @ commands.has_any_role(*COGS_CONFIG.getlist("test_playground", 'allowed_roles'))
    @in_allowed_channels(set(COGS_CONFIG.getlist("test_playground", 'allowed_channels')))
    async def check_date_converter(self, ctx, in_date: DateOnlyConverter):
        year = in_date.year
        month = in_date.month
        day = in_date.day
        hour = in_date.hour
        minute = in_date.minute
        second = in_date.second

        await ctx.send(f"__year:__ {year} | __month:__ {month} | __day:__ {day} || __hour:__ {hour} | __minute:__ {minute} | __second:__ {second}")

    async def correct_template(self, template_content, item_data):
        new_content = template_content
        for item in item_data:
            if item.has_error is True and item.is_case_error is True:
                new_content = new_content.replace(f'"{item.item}"', f'"{item.correction}"')
        return new_content

    @commands.command(aliases=get_aliases("check_template"))
    @ allowed_channel_and_allowed_role(CONFIG_NAME, True, allowed_in_dm_key='check_template_allowed_in_dm')
    @has_attachments(1)
    async def check_template(self, ctx, all_items_file=True, case_insensitive: bool = False):
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.sqf'):

            await ctx.send(await self.bot.get_antistasi_emoji("Salute"))

            async with ctx.typing():
                await asyncio.sleep(2)
                attachment_data = await attachment.read()
                attachment_data = attachment_data.decode('utf-8', errors='ignore')
                found_data = await self.bot.execute_in_thread(template_checker_run, attachment_data, case_insensitive)
                found_data_amount_errors = found_data.get('found_errors')
                found_data = found_data.get('items')
                description = "**__NO__** errors in this Template File"
                if found_data_amount_errors > 0:
                    if found_data_amount_errors > 1:
                        description = f"{found_data_amount_errors} errors in this file"
                    else:
                        description = f"{found_data_amount_errors} error in this file"

                embed = discord.Embed(title=f"Template Check: {attachment.filename}", description=description,
                                      color=self.support.color('OLIVE_DRAB_0x7'.casefold()).discord_color, timestamp=datetime.now(tz=timezone("Europe/Berlin")))
                embed.set_thumbnail(url="https://s3.amazonaws.com/files.enjin.com/1218665/site_logo/NEW%20LOGO%20BANNER.png")

                if found_data_amount_errors != 0:
                    embed.add_field(name="Corrected file", value="I have attached the corrected file", inline=False)
                    embed.add_field(name="Case Errors", value=f"\n{ZERO_WIDTH}I only corrected case errors", inline=False)
                    embed.add_field(name="Not corrected was:\n" + ZERO_WIDTH,
                                    value='\n'.join([error_item.item for error_item in found_data if error_item.has_error is True and (error_item.is_case_error is False or error_item.correction == "FILEPATH")]) + '\n' + ZERO_WIDTH, inline=False)
                    code_message = [f"{'#'*34}\n{'#'*10} FOUND ERRORS {'#'*10}\n{'#'*34}\n"]

                    sep_one = max(map(len, [item.item for item in found_data if item.has_error is True])) + 3
                    for index, error_item in enumerate(found_data):
                        if error_item.has_error:
                            case_error = 'Yes' if error_item.is_case_error is True else 'No'
                            possible_correction = '' if error_item.correction is None else f'| possible correction =      "{error_item.correction}"'
                            has_error = f' | error =    Yes   | is case error = {case_error}{" "*(6-len(case_error))} {possible_correction}'
                            start_sign = '++ '
                            code_message.append(start_sign + f'item =        "{error_item.item}"{" " * (sep_one - len(error_item.item))} | line number =    {str(error_item.line_number)} {" " * (6 - len(str(error_item.line_number)))} {has_error}\n')

                    await self.bot.split_to_messages(ctx, message='\n'.join(code_message + ['\n' + ZERO_WIDTH]), in_codeblock=True, syntax_highlighting='ml')

                    await asyncio.sleep(1)
                    new_content = await self.correct_template(attachment_data, found_data)
                    new_file_name = attachment.filename.replace('.sqf', '_CORRECTED.sqf')
                    with StringIO() as io_fp:
                        io_fp.write(new_content)
                        io_fp.seek(0)
                        _file = discord.File(io_fp, new_file_name)

                        await ctx.send(file=_file)
                else:
                    await ctx.reply(file=discord.File(APPDATA["Congratulations.mp3"], spoiler=True))
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
                if all_items_file is True:
                    with StringIO() as io_fp:
                        io_fp.write(f"ALL ITEMS FROM FILE '{attachment.filename}'")
                        sorted_found_data = sorted(found_data, key=lambda x: (1 if x.has_error else 99, x.line_number))
                        for item in found_data:

                            case_error = 'yes' if item.is_case_error is True else 'no'
                            possible_correction = '' if item.correction is None else f'| possible correction: "{item.correction}"'
                            has_error = f' | error: yes | is case error: {case_error}{" "*(5-len(case_error))} {possible_correction}'

                            io_fp.write(
                                f'item: "{item.item}"{" "*(50-len(item.item))} | line number: {str(item.line_number)}{" "*(5-len(str(item.line_number)))} {has_error}\n')
                        io_fp.seek(0)
                        _all_item_file = discord.File(io_fp, attachment.filename.replace('.sqf', '_ALL_ITEMS.sqf'))

                        await ctx.send(file=_all_item_file)
                        await asyncio.sleep(5)

    @ commands.command(aliases=get_aliases("random_embed_color"))
    @ allowed_channel_and_allowed_role("test_playground")
    async def random_embed_color(self, ctx):
        color = self.bot.support.random_color
        embed = discord.Embed(title='test', description=color.name, color=color.int)
        await ctx.send(embed=embed)

    @ commands.command(aliases=get_aliases("send_all_colors_file"))
    @ allowed_channel_and_allowed_role("test_playground")
    async def send_all_colors_file(self, ctx):
        _file = discord.File(str(self.bot.support.all_colors_json_file), os.path.basename(str(self.bot.support.all_colors_json_file)))
        await ctx.send('here', file=_file)

    @ commands.command(aliases=get_aliases("check_flags"))
    @ allowed_channel_and_allowed_role("test_playground")
    async def check_flags(self, ctx, flags: Greedy[FlagArg(['make_embed', 'random_color'])], ending: str):
        print(flags)
        if 'make_embed' in flags:
            color = discord.Embed.Empty
            if 'random_color' in flags:
                color = self.bot.support.random_color.int
            embed = discord.Embed(title='check flags', description=ending, color=color)
            await ctx.send(embed=embed)
        else:
            await ctx.send(ending)

    @ commands.command(aliases=get_aliases("test_dyn_time"))
    @ allowed_channel_and_allowed_role("test_playground")
    async def test_dyn_time(self, ctx):
        embed = discord.Embed(title='testing dynamic timestamp', description='Could you please post under this message the time you see as timestamp of this Embed? (just copy paste)', timestamp=datetime.now(tz=timezone('Europe/Vienna')))
        await ctx.send(embed=embed)

    async def find_all_template_files(self, channel):
        async for message in channel.history(limit=None):
            if len(message.attachments) >= 1:
                attachment = message.attachments[0]
                if attachment.filename.endswith('.sqf'):
                    yield message

    @ commands.command(aliases=get_aliases("get_all_template_messages"))
    @ allowed_channel_and_allowed_role("test_playground")
    async def get_all_template_messages(self, ctx):

        channel = await self.bot.fetch_channel(785935400467824651)
        async for message in self.find_all_template_files(channel):
            await self.check_template_iter_file(ctx, message.attachments[0])
            await asyncio.sleep(5)

    async def check_template_iter_file(self, ctx, file, case_insensitive: bool = False):
        _file = file
        with ctx.typing():
            with TemporaryDirectory() as tempdir:
                tempfile_path = pathmaker(tempdir, _file.filename)
                await _file.save(tempfile_path)
                case = '--case-insensitive' if case_insensitive is True else '--case-sensitive'
                func = partial(subprocess.run, [APPDATA["antistasi_template_checker.exe"], 'from_file', '-np', case, tempfile_path], check=True, capture_output=True)
                cmd = await self.bot.execute_in_thread(func)
                _output = cmd.stdout.decode('utf-8', errors='replace')
                # await self.bot.split_to_messages(ctx, _output, in_codeblock=True)
                new_file_name = _file.filename.replace(os.path.splitext(_file.filename)[-1], '_CORRECTED' + os.path.splitext(_file.filename)[-1])
                new_file_path = pathmaker(tempdir, new_file_name)
                if os.path.isfile(new_file_path):
                    _new_file = discord.File(new_file_path, new_file_name)
                    await ctx.send('The Corrected File', file=_new_file)

    @commands.command(aliases=get_aliases('search_usernames'))
    @allowed_channel_and_allowed_role(CONFIG_NAME, in_dm_allowed=True, allowed_roles_key='roles_restricted_command', allowed_in_dm_key="search_usernames_dm_allowed")
    @log_invoker(log, 'critical')
    async def search_usernames(self, ctx, *, names: str):
        full_match = {}
        partial_match = {}
        similar_match = {}
        to_match_names = names.split(',')
        to_match_names = set(map(lambda x: x.strip().casefold(), to_match_names))
        user_list = self.bot.users
        for user in user_list:
            for name in to_match_names:
                if name not in full_match:
                    full_match[name] = []
                if name not in partial_match:
                    partial_match[name] = []
                if name == user.name.casefold():
                    full_match[name].append(user.name)
                elif name in user.name.casefold():
                    partial_match[name].append(user.name)
        # for match_name in to_match_names:
        #     fuzz_result = fuzzprocess.extract(match_name, [user.name for user in user_list])
        #     if fuzz_result:
        #         similar_match[match_name] = fuzz_result
        await ctx.reply("__**Full Matches**__")
        await self.bot.split_to_messages(ctx, pformat(full_match).replace('{', '').replace('}', ''))
        await ctx.reply("__**Partial Matches**__")
        await self.bot.split_to_messages(ctx, pformat(partial_match).replace('{', '').replace('}', ''))
        await ctx.reply("__**all user I can see**__")
        await self.bot.split_to_messages(ctx, '\n'.join([user.name for user in user_list]), in_codeblock=True)

    @commands.command()
    @allowed_channel_and_allowed_role(CONFIG_NAME)
    @log_invoker(log, 'debug')
    async def embed_experiment(self, ctx):

        await ctx.send(**await self.bot.make_generic_embed(author='bot_author', footer='feature_request_footer', description="this is and test"))


# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        log.debug("Cog '%s' UNLOADED!", str(self))
# endregion [SpecialMethods]


def setup(bot):
    bot.add_cog(TestPlaygroundCog(bot))