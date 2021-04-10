
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
from tempfile import TemporaryDirectory
import asyncio
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory
from textwrap import dedent
from datetime import datetime, timedelta
from typing import Iterable, Union, List
# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
from fuzzywuzzy import process as fuzzprocess
import discord
from io import StringIO
from discord.ext import commands, tasks
from webdav3.client import Client
from async_property import async_property
from dateparser import parse as date_parse
from pytz import timezone
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.misc import CogConfigReadOnly, make_config_name
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker, allowed_channel_and_allowed_role, has_attachments
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.engine.replacements import auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_antistasi_log_watcher_cog import LogServer
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from antistasi_template_checker.engine.antistasi_template_parser import run as template_checker_run
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH

if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)

# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

COG_NAME = "TemplateCheckerCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]

_from_cog_config = CogConfigReadOnly(CONFIG_NAME)

# endregion [Helper]


class TemplateCheckerCog(commands.Cog, command_attrs={'name': COG_NAME}):
    """
    soon
    """
# region [ClassAttributes]

    config_name = CONFIG_NAME
    already_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.OUTDATED | CogState.CRASHING | CogState.EMPTY | CogState.DOCUMENTATION_MISSING,
                             "2021-02-18 11:00:11")}

    required_config_data = dedent("""

                                    """).strip('\n')
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):

        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]


    async def correct_template(self, template_content, item_data):
        new_content = template_content
        for item in item_data:
            if item.has_error is True and item.is_case_error is True:
                new_content = new_content.replace(f'"{item.item}"', f'"{item.correction}"')
        return new_content

    @auto_meta_info_command(enabled=get_command_enabled("check_template"))
    @allowed_channel_and_allowed_role()
    @has_attachments(1)
    async def check_template(self, ctx, all_items_file=True, case_insensitive: bool = False):
        """
        Checks all Classnames inside a provided template.

        Needs to have the tempalte as attachment to the invoking message.

        Returns the list of classnames it can't find in the config along with possible correction.

        Returns also a corrected version of the template file.

        Args:
            all_items_file (bool, optional): if it should also provide a file that lists all used classes. Defaults to True.
            case_insensitive (bool, optional): if it should check Case insentive. Defaults to False.
        """
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

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

# endregion [HelperMethods]

# region [SpecialMethods]

    def cog_check(self, ctx):
        return True

    async def cog_command_error(self, ctx, error):
        pass

    async def cog_before_invoke(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        pass

    def cog_unload(self):

        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.qualified_name}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(TemplateCheckerCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
