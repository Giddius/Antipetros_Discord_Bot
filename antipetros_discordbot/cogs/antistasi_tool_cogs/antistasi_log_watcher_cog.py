
# region [Imports]

# * Standard Library Imports -->
import os
from typing import TYPE_CHECKING
from tempfile import TemporaryDirectory
import asyncio
from zipfile import ZipFile, ZIP_LZMA
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import List, Union
from contextlib import asynccontextmanager
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
from discord.ext import commands, tasks
from webdav3.client import Client
from async_property import async_property
from dateparser import parse as date_parse
import pytz
from jinja2 import Environment, FileSystemLoader
# * Gid Imports -->
import gidlogger as glog
from weasyprint import HTML
# * Local Imports -->
from antipetros_discordbot.utility.misc import async_dict_items_iterator, async_list_iterator, async_write_it
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, writeit
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.auxiliary_classes.for_cogs.aux_antistasi_log_watcher_cog import LogServer
from antipetros_discordbot.utility.nextcloud import get_nextcloud_options
from io import BytesIO, StringIO
from antipetros_discordbot.utility.general_decorator import universal_log_profiler
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

# endregion[Constants]


class AntistasiLogWatcherCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.DEVTOOLS | CommandCategory.ADMINTOOLS}):
    """
    Different interactions with saved Antistasi Community Server Logs. Works by connecting to and interacting with the Online Storage where the logs are saved.
    """
# region [ClassAttributes]
    public = True

    already_notified_savefile = pathmaker(APPDATA["json_data"], "notified_log_files.json")

    required_config_data = {'base_config': {},
                            'cogs_config': {"log_file_warning_size_threshold": "200mb",
                                            "max_amount_get_files": 5}}
    required_files = [RequiredFile(already_notified_savefile, [], RequiredFile.FileType.JSON)]
    meta_status = CogMetaStatus.WORKING | CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.DOCUMENTATION_MISSING
# endregion [ClassAttributes]

# region [Init]
    @universal_log_profiler
    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.server_items = {}
        self.ready = False
        self.meta_data_setter('docstring', self.docstring)

        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    @universal_log_profiler
    def already_notified(self):
        if os.path.exists(self.already_notified_savefile) is False:
            writejson([], self.already_notified_savefile)
        return loadjson(self.already_notified_savefile)

    @universal_log_profiler
    async def add_to_already_notified(self, data: Union[str, list, set, tuple], overwrite=False):
        if overwrite is True:
            write_data = data
        elif isinstance(data, (list, set, tuple)):
            data = list(data)
            write_data = self.already_notified + data
        elif isinstance(data, str):
            write_data = self.already_notified
            write_data.append(data)
        writejson(write_data, self.already_notified_savefile)

    @property
    @universal_log_profiler
    def old_logfile_cutoff_date(self):
        time_text = COGS_CONFIG.retrieve(self.config_name, 'log_file_cutoff', typus=str, direct_fallback='5 days')
        return date_parse(time_text, settings={'TIMEZONE': 'UTC'})

    @async_property
    @universal_log_profiler
    async def member_to_notify(self):
        member_ids = COGS_CONFIG.retrieve(self.config_name, 'member_id_to_notify_oversized', typus=List[int], direct_fallback=[])
        return [await self.bot.fetch_antistasi_member(member_id) for member_id in member_ids]

    @property
    @universal_log_profiler
    def size_limit(self):
        return COGS_CONFIG.retrieve(self.config_name, 'log_file_warning_size_threshold', typus=str, direct_fallback='200mb')

# endregion [Properties]

# region [Setup]

    @universal_log_profiler
    async def on_ready_setup(self):
        asyncio.create_task(self.get_base_structure())

        self.update_log_file_data_loop.start()
        self.ready = await asyncio.sleep(5, True)
        log.debug('setup for cog "%s" finished', str(self))

    @universal_log_profiler
    async def update(self, typus: UpdateTypus):
        return
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=5, reconnect=True)
    @universal_log_profiler
    async def update_log_file_data_loop(self):
        if self.ready is False:
            return

        await self.update_log_file_data()
        asyncio.create_task(self.check_oversized_logs())

    @update_log_file_data_loop.error
    async def update_log_file_data_loop_error_handler(self, error):
        log.error(error, exc_info=True)
        await self.bot.message_creator(error)
        if self.update_log_file_data_loop.is_running() is False:
            await self.get_base_structure()
            self.update_log_file_data_loop.restart()

    @universal_log_profiler
    async def update_log_file_data(self):
        async for folder_name, folder_item in async_dict_items_iterator(self.server):
            log.debug("updating log files for '%s'", folder_name)
            await folder_item.update()
            await folder_item.sort()

    @universal_log_profiler
    async def check_oversized_logs(self):
        async for folder_name, folder_item in async_dict_items_iterator(self.server):
            log.debug("checking log files of '%s', for oversize", folder_name)
            oversize_items = await folder_item.get_oversized_items()

            oversize_items = [log_item for log_item in oversize_items if log_item.etag not in self.already_notified]
            async for item in async_list_iterator(oversize_items):
                if item.modified.replace(tzinfo=pytz.UTC) > self.old_logfile_cutoff_date.replace(tzinfo=pytz.UTC):
                    await self.notify_oversized_log(item)
                await self.add_to_already_notified(item.etag)


# endregion [Loops]

# region [Listener]


# endregion [Listener]

# region [Commands]

    @universal_log_profiler
    def _transform_mod_name(self, mod_name: str):
        mod_name = mod_name.removeprefix('@')
        return mod_name

    @asynccontextmanager
    async def get_newest_mod_data_only_file(self, server: str = 'mainserver_1'):
        mod_server = server if server in self.server else fuzzprocess.extractOne(server, list(self.server))[0]
        folder_item = self.server[mod_server]
        log_item = await folder_item.get_newest_log_file('Server', 1)
        log_item = log_item[0]
        mod_data = await log_item.mod_data
        templ_data = []
        template = await asyncio.to_thread(self.jinja_env.get_template, 'arma_required_mods.html.jinja')
        for item in mod_data:
            transformed_mod_name = self._transform_mod_name(item)
            templ_data.append(self.mod_lookup_data.get(transformed_mod_name))

        html_string = template.render(req_mods=templ_data, server_name=server.replace('_', ' '))
        html_path = pathmaker(APPDATA['temp_files'], f"{server}_mods.html")
        writeit(html_path, html_string)
        html_file = discord.File(html_path)

        weasy_html = HTML(string=html_string)
        image_path = pathmaker(APPDATA['temp_files'], f"{server}_mods.png")
        weasy_html.write_png(image_path, optimize_images=True, presentational_hints=True, resolution=125)

        yield (html_file, image_path)
        os.remove(image_path)
        os.remove(html_path)

    @auto_meta_info_command(aliases=['mods', 'mods?', 'mod_list', 'mod_list?'], categories=CommandCategory.GENERAL)
    @allowed_channel_and_allowed_role()
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def get_newest_mod_data(self, ctx: commands.Context, server: str = 'mainserver_1'):
        """
        Gets the required mods for the Server.

        Provides the list as embed and Arma3 importable html file.

        Args:
            server (str): Name of the Antistasi Community Server to retrieve the mod list.

        Example:
            @AntiPetros get_newest_mod_data mainserver_1
        """
        mod_server = server if server in self.server else fuzzprocess.extractOne(server, list(self.server))[0]
        folder_item = self.server[mod_server]
        log_item = await folder_item.get_newest_log_file('Server', 1)
        log_item = log_item[0]
        mod_data = await log_item.mod_data
        templ_data = []
        for item in mod_data:
            transformed_mod_name = self._transform_mod_name(item)
            templ_data.append(self.mod_lookup_data.get(transformed_mod_name))

        template = self.jinja_env.get_template('arma_required_mods.html.jinja')
        values = []
        for item in templ_data:
            try:
                values.append(f"- {item.get('name')}")
            except AttributeError:
                continue
        embed_data = await self.bot.make_generic_embed(title=f"Mods currently on the {server}", description='```diff\n' + '\n------------\n'.join(item for item in values) + '\n```')
        with TemporaryDirectory() as tempdir:
            html_path = pathmaker(tempdir, f"{mod_server}_mods.html")
            writeit(html_path, template.render(req_mods=templ_data, server_name=server.replace('_', ' ')))
            html_file = discord.File(html_path)
            await ctx.send(**embed_data)
            await ctx.send(file=html_file)

    @auto_meta_info_command(aliases=['as_logs', 'server_logs', 'get_logs', 'get_log'], categories=CommandCategory.DEVTOOLS | CommandCategory.ADMINTOOLS)
    @allowed_channel_and_allowed_role()
    async def get_newest_logs(self, ctx, server: str = 'mainserver_1', sub_folder: str = 'server', amount: int = 1):
        """
        Gets the newest log files from the Dev Drive.

        If the log file is bigger than current file size limit, it will provide it zipped.

        Tries to fuzzy match both server and sub-folder.

        Args:
            server (str): Name of the Server
            sub_folder (str): Name of the sub-folder e.g. Server, HC_0, HC_1,...
            amount (int, optional): The amount of log files to get. standard max is 5 . Defaults to 1.

        Example:
            @AntiPetros get_newest_logs mainserver_1 server
        """
        max_amount = COGS_CONFIG.retrieve(self.config_name, 'max_amount_get_files', typus=int, direct_fallback=5)
        if amount > max_amount:
            await ctx.send(f'You requested more files than the max allowed amount of {max_amount}, aborting!')
            return
        server = server.casefold()
        server = server if server in self.server else fuzzprocess.extractOne(server, list(self.server))[0]
        folder_item = self.server[server]
        sub_folder = sub_folder if sub_folder in folder_item.sub_folder else fuzzprocess.extractOne(sub_folder, list(folder_item.sub_folder))[0]
        try:
            async for log_item in async_list_iterator(await folder_item.get_newest_log_file(sub_folder, amount)):
                with TemporaryDirectory() as tempdir:
                    file_path = await log_item.download(tempdir)
                    if log_item.size >= self.bot.filesize_limit:
                        file_path = await self.zip_log_file(file_path)
                    file = discord.File(file_path)
                    embed_data = await self.bot.make_generic_embed(title=log_item.name,
                                                                   description=f"{log_item.server_name}/{log_item.sub_folder_name}",
                                                                   fields=[self.bot.field_item(name="__**Size:**__", value=log_item.size_pretty, inline=False),
                                                                           self.bot.field_item(name="__**Created at:**__", value=log_item.created_pretty, inline=False),
                                                                           self.bot.field_item(name="__**Last Modified:**__", value=log_item.modified_pretty, inline=False),
                                                                           self.bot.field_item(name="__**Last Modified Local Time:**__", value="SEE TIMESTAMP AT THE BOTTOM", inline=False)],
                                                                   timestamp=log_item.modified,
                                                                   thumbnail='log_file')
                    await ctx.send(**embed_data, file=file)
        except KeyError as error:
            await ctx.send(str(error))
# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]
    @universal_log_profiler
    async def zip_log_file(self, file_path):
        zip_path = pathmaker(os.path.dirname(file_path), os.path.basename(file_path).split('.')[0] + '.zip')
        with ZipFile(zip_path, 'w', ZIP_LZMA) as zippy:
            await asyncio.to_thread(zippy.write, file_path, os.path.basename(file_path))
        return zip_path

    @universal_log_profiler
    async def get_base_structure(self):
        nextcloud_client = Client(get_nextcloud_options())
        async for folder in async_list_iterator(await asyncio.to_thread(nextcloud_client.list, self.nextcloud_base_folder)):
            folder = folder.strip('/')
            if folder != self.nextcloud_base_folder and '.' not in folder:
                folder_item = LogServer(self.nextcloud_base_folder, folder)
                await folder_item.get_data()
                self.server[folder.casefold()] = folder_item
            await asyncio.sleep(0)
        log.info(str(self) + ' collected server names: ' + ', '.join([key for key in self.server]))

    @universal_log_profiler
    async def notify_oversized_log(self, log_item):
        async for member in async_list_iterator(await self.member_to_notify):
            embed_data = await self.bot.make_generic_embed(title="Warning Oversized Log File",
                                                           description=f"Log file `{log_item.name}` from server `{log_item.server_name}` and subfolder `{log_item.sub_folder_name}`, is over the size limit of `{self.size_limit}`",
                                                           fields=[self.bot.field_item(name="__**Current Size**__", value=log_item.size_pretty),
                                                                   self.bot.field_item(name="__**Last modified**__", value=log_item.modified_pretty)],
                                                           thumbnail="warning",
                                                           footer=None)
            await member.send(**embed_data)

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
        self.update_log_file_data_loop.stop()

        log.debug("Cog '%s' UNLOADED!", str(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(AntistasiLogWatcherCog(bot))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
