# jinja2: trim_blocks:True
# jinja2: lstrip_blocks :True
# region [Imports]

# * Standard Library Imports -->
import os
from typing import List
from typing import TYPE_CHECKING

# * Third Party Imports -->
# import requests
# import pyperclip
# import matplotlib.pyplot as plt
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from github import Github, GithubException
# from jinja2 import BaseLoader, Environment
# from natsort import natsorted
# from fuzzywuzzy import fuzz, process
import discord
from discord.ext import commands
from discord import ChannelType
import tldextract
from textwrap import dedent
from icecream import ic
# * Gid Imports -->
import gidlogger as glog

# * Local Imports -->
from antipetros_discordbot.utility.enums import RequestStatus
from antipetros_discordbot.utility.named_tuples import ListenerContext

from antipetros_discordbot.utility.gidtools_functions import pathmaker, writejson
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.misc import make_config_name, make_full_cog_id
from antipetros_discordbot.utility.checks import allowed_requester, command_enabled_checker
from antipetros_discordbot.utility.enums import CogState, UpdateTypus
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot


# endregion[Imports]

# region [TODO]

# TODO: create "on_message" and "on_message_edit" listener to check for urls
# TODO: create method to find urls in messages

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
COG_NAME = "SecurityCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]

# region [Helper]


# endregion [Helper]


class SecurityCog(commands.Cog, command_attrs={'name': COG_NAME, "description": ""}):
    """
    [summary]

    [extended_summary]

    """
# region [ClassAttributes]
    cog_id = 685
    full_cog_id = make_full_cog_id(THIS_FILE_DIR, cog_id)
    config_name = CONFIG_NAME
    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.OPEN_TODOS | CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.NEEDS_REFRACTORING | CogState.OUTDATED | CogState.CRASHING,
                             "2021-02-06 05:18:25",
                             "917274ca9966d8de3909eb5ac74869405c35f062db243440215e4f956b8e6beddd9cc812fe7e2f1b64fc93cf4b690f060c2b1da0e2f3aab6b39afe2f727013e1")}
    required_config_data = dedent("""
                                        blocklist_hostfile_urls = https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts, https://raw.githubusercontent.com/Ultimate-Hosts-Blacklist/Ultimate.Hosts.Blacklist/master/hosts/hosts0

                                        forbidden_mime_types = application/zip,
                                            application/x-tar,
                                            application/x-rar,
                                            application/x-msi,
                                            application/x-gzip,
                                            application/x-dosexec,
                                            application/x-7z-compressed,
                                            text/x-java,
                                            text/x-msdos-batch,
                                            text/x-python,
                                            video/mp4,
                                            video/mpeg
                                        forbidden_file_extensions = exe, zip, 7z, rar, xz, bat, cmd, sh, js, py, mp4, mpeg, mp4, mp3

                                        attachment_scanner_listener_enabled = no

                                        attachment_scanner_listener_allowed_channels = suggestions, bot-testing

                                        attachment_scanner_listener_exclude_roles = Dev Helper, Admin

                                        link_scanner_listener_enabled = no

                                        link_scanner_listener_allowed_channels = suggestions, bot-testing

                                        link_scanner_listener_exclude_roles = Dev Helper, Admin


                                        """)

    bad_links_json_file = pathmaker(APPDATA['json_data'], 'forbidden_link_list.json')
# endregion [ClassAttributes]

# region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        self.bot = bot
        self.support = self.bot.support
        self.bad_links = None
        self.blocklist_hostfile_urls = COGS_CONFIG.retrieve(self.config_name, 'blocklist_hostfile_urls', typus=List[str])
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def forbidden_extensions(self):
        return [ext.casefold() for ext in COGS_CONFIG.retrieve(self.config_name, 'forbidden_file_extensions', typus=list, direct_fallback=[])]

    @property
    def forbidden_mime_types(self):
        return COGS_CONFIG.retrieve(self.config_name, 'forbidden_mime_types', typus=list, direct_fallback=[])


# endregion [Properties]

# region [Setup]


    async def on_ready_setup(self):
        await self._create_forbidden_link_list()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        if UpdateTypus.TIME in typus:
            await self._create_forbidden_link_list()
        else:
            return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @ commands.Cog.listener(name="on_message")
    async def attachment_scanner_listener(self, message: discord.Message):
        await self.bot.wait_until_ready()
        if message.channel.type is not ChannelType.text:
            return
        if get_command_enabled("attachment_scanner_listener") is False or len(message.attachments) == 0 or await self._attachment_scanner_exclusion_check(message) is True:
            return
        listener_context = ListenerContext(message=message,
                                           content=message.content,
                                           channel=message.channel,
                                           author=message.author,
                                           creation_time=message.created_at,
                                           reactions=message.reactions,
                                           attachments=message.attachments)

        for attachment in listener_context.attachments:
            filename = attachment.filename
            extension = filename.split('.')[-1]
            if extension.casefold() in self.forbidden_extensions:
                await self._handle_forbidden_attachment(listener_context, filename)
                return


# endregion [Listener]

# region [Commands]

# endregion [Commands]

# region [DataStorage]

# endregion [DataStorage]

# region [HelperMethods]

    async def _process_raw_blocklist_content(self, raw_content):
        """
        Process downloaded Blacklist to a list of raw urls.

        Returns:
            set: forbidden_link_list as set for quick contain checks
        """

        _out = []
        if self.bot.is_debug is True:
            raw_content += '\n\n0 www.stackoverflow.com'  # added for Testing
        for line in raw_content.splitlines():
            if line.startswith('0') and line not in ['', '0.0.0.0 0.0.0.0']:
                forbidden_url = line.split(' ')[-1].strip()
                forbidden_url = forbidden_url.split('#')[0].strip()
                _out.append(forbidden_url.strip().casefold())
        return _out

    async def _create_forbidden_link_list(self):
        """
        Downloads Blacklist and saves it to json, after processing (-->_process_raw_blocklist_content)
        """
        forbidden_links = []
        for source_hostdata_url in self.blocklist_hostfile_urls:
            async with self.bot.aio_request_session.get(source_hostdata_url) as _response:
                if RequestStatus(_response.status) is RequestStatus.Ok:
                    _content = await _response.read()
                    _content = _content.decode('utf-8', errors='ignore')
                    forbidden_links += await self._process_raw_blocklist_content(_content)
                    log.debug("downloaded host file '%s'", source_hostdata_url)

        forbidden_links = list(set(forbidden_links))
        forbidden_links = sorted(forbidden_links, key=lambda x: x.split('.')[-1])
        log.debug("writing link blacklist to json file")
        writejson(forbidden_links, self.bad_links_json_file)
        self.bad_links = forbidden_links
        log.info("creating link blacklist completed")

    async def _handle_forbidden_attachment(self, listener_context: ListenerContext, filename: str):
        await listener_context.message.delete()
        await listener_context.channel.send(listener_context.author.mention + ' Your message was deleted as you tried to send a forbidden type of attachment')

    async def _attachment_scanner_exclusion_check(self, msg):
        allowed_roles = [role_name.casefold() for role_name in COGS_CONFIG.retrieve("security", 'attachment_scanner_listener_exclude_roles', typus=list, direct_fallback=[])]
        if any(role.name.casefold() in allowed_roles for role in msg.author.roles):
            return True
        if msg.channel.name.casefold() not in [channel_name.casefold() for channel_name in COGS_CONFIG.retrieve("security", 'attachment_scanner_listener_allowed_channels', typus=list, direct_fallback=[])]:
            return True
        return False

    async def check_link(self, url):
        extracted_url = tldextract.extract(url)
        cleaned_url = f"{extracted_url.domain}.{extracted_url.suffix}".casefold()
        for bad_url in self.bad_links:
            if cleaned_url == bad_url:
                return True, bad_url
        return False, None

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
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.__class__.__name__


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(SecurityCog(bot)))


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
