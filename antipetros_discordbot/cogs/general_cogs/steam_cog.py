
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from datetime import datetime
import random
import secrets
import typing
import asyncio
from urllib.parse import quote as urlquote
from textwrap import dedent
from collections import namedtuple
import re
# * Third Party Imports --------------------------------------------------------------------------------->
from pytz import timezone, country_timezones
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess
from discord.ext import flags, tasks, commands
from discord import AllowedMentions
import discord

from pyfiglet import Figlet
from bs4 import BeautifulSoup
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
import aiohttp
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.cogs import get_aliases, get_doc_data
from antipetros_discordbot.utility.misc import STANDARD_DATETIME_FORMAT, save_commands, CogConfigReadOnly, make_config_name, is_even
from antipetros_discordbot.utility.checks import command_enabled_checker, allowed_requester, allowed_channel_and_allowed_role_2
from antipetros_discordbot.utility.named_tuples import CITY_ITEM, COUNTRY_ITEM
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.discord_markdown_helper.the_dragon import THE_DRAGON
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
from antipetros_discordbot.utility.poor_mans_abc import attribute_checker
from antipetros_discordbot.utility.enums import RequestStatus, CogState
from antipetros_discordbot.utility.replacements.command_replacement import auto_meta_info_command
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)


# endregion[Logging]

# region [Constants]

APPDATA = ParaStorageKeeper.get_appdata()
BASE_CONFIG = ParaStorageKeeper.get_config('base_config')
COGS_CONFIG = ParaStorageKeeper.get_config('cogs_config')
# location of this file, does not work if app gets compiled to exe with pyinstaller
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

COG_NAME = "SteamCog"

CONFIG_NAME = make_config_name(COG_NAME)

get_command_enabled = command_enabled_checker(CONFIG_NAME)

# endregion[Constants]


class SteamCog(commands.Cog, command_attrs={'hidden': False, "name": COG_NAME}):
    """
    Soon
    """
    # region [ClassAttributes]
    config_name = CONFIG_NAME

    docattrs = {'show_in_readme': True,
                'is_ready': (CogState.UNTESTED | CogState.FEATURE_MISSING | CogState.CRASHING | CogState.DOCUMENTATION_MISSING,
                             "2021-02-06 03:32:39",
                             "05703df4faf098a7f3f5cea49c51374b3225162318b081075eb0745cc36ddea6ff11d2f4afae1ac706191e8db881e005104ddabe5ba80687ac239ede160c3178")}

    required_config_data = dedent("""
                                  """)

    base_url = "https://steamcommunity.com/sharedfiles/filedetails/?id="

    registered_workshop_items_file = pathmaker(APPDATA['json_data'], 'registered_steam_workshop_items.json')

    month_map = {'jan': 1,
                 'feb': 2,
                 'mar': 3,
                 "apr": 4,
                 'may': 5,
                 'jun': 6,
                 'jul': 7,
                 'aug': 8,
                 'sep': 9,
                 'oct': 10,
                 'nov': 11,
                 'dec': 12}
    image_link_regex = re.compile(r"(?<=\')(?P<image_link>.*)(?=\')")
    workshop_item = namedtuple("WorkshopItem", ['title', 'updated', 'requirements', 'url', "image_link", "size", "id"])
    date_time_format = "%Y-%m-%d %H:%M"
    # endregion [ClassAttributes]

    # region [Init]

    def __init__(self, bot):
        self.bot = bot
        self.support = self.bot.support
        self.allowed_channels = allowed_requester(self, 'channels')
        self.allowed_roles = allowed_requester(self, 'roles')
        self.allowed_dm_ids = allowed_requester(self, 'dm_ids')
        if os.path.isfile(self.registered_workshop_items_file) is False:
            writejson([], self.registered_workshop_items_file)
        glog.class_init_notification(log, self)

# endregion [Init]

# region [Properties]

    @property
    def registered_workshop_items(self):
        return [self.workshop_item(**item) for item in loadjson(self.registered_workshop_items_file)]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        self.check_for_updates.start()
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus):
        return
        log.debug('cog "%s" was updated', str(self))


# endregion [Setup]

# region [Loops]

    @tasks.loop(minutes=5, reconnect=True)
    async def check_for_updates(self):
        for item in self.registered_workshop_items:
            log.debug("checking steam_workshop_item '%s' for possible update", item.title)
            new_item = await self._get_fresh_item_data(item.id)
            updated_new = datetime.strptime(new_item.updated, self.date_time_format)
            updated_old = datetime.strptime(item.updated, self.date_time_format)
            log.debug("comapring time '%s' new, to '%s' old", updated_new.strftime(self.date_time_format), updated_old.strftime(self.date_time_format))
            if updated_new > updated_old:
                await self._update_item_in_registered_items(item, new_item)
                await self.notify_update(item, new_item)

# endregion [Loops]
# region [Listener]
# endregion [Listener]
# region [Commands]

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role_2()
    async def register_workshop_item(self, ctx, item_ids: commands.Greedy[int]):
        for item_id in item_ids:
            item = await self._get_fresh_item_data(item_id)
            saved = await self._add_item_to_registered_items(item)
            if saved is False:
                await ctx.send(f'Item "{item.title}" with id "{item.id}" already registered!')
                return
            req_value = '\n'.join([f"**{req_name}**\n{req_link}" for req_name, req_link in item.requirements]) if len(item.requirements) > 0 else 'No Requirements'
            fields = [self.bot.field_item(name="Last Updated:", value=item.updated, inline=False),
                      self.bot.field_item(name='Requirements:', value=req_value, inline=False),
                      self.bot.field_item(name="Size:", value=item.size, inline=False)]

            embed_data = await self.bot.make_generic_embed(author={'name': "link to steam workshop page 🔗", 'url': item.url, 'icon_url': item.image_link}, title=item.title, description="was added to registered Workshop Items", image=item.image_link,
                                                           fields=fields, thumbnail=None)

            await ctx.send(**embed_data)

    @auto_meta_info_command()
    @allowed_channel_and_allowed_role_2()
    async def get_workshop_item_data(self, ctx, item_id: int):
        item = await self._get_fresh_item_data(item_id)
        req_value = '\n'.join([f"**{req_name}**\n{req_link}" for req_name, req_link in item.requirements]) if len(item.requirements) > 0 else 'No Requirements'
        fields = [self.bot.field_item(name="Last Updated:", value=item.updated, inline=False),
                  self.bot.field_item(name='Requirements:', value=req_value, inline=False),
                  self.bot.field_item(name="Size:", value=item.size, inline=False)]

        embed_data = await self.bot.make_generic_embed(author={'name': "link to steam workshop page 🔗", 'url': item.url, 'icon_url': item.image_link}, title=item.title, image=item.image_link,
                                                       fields=fields, thumbnail=None)

        await ctx.send(**embed_data)
# endregion [Commands]
# region [DataStorage]
# endregion [DataStorage]
# region [Embeds]
# endregion [Embeds]
# region [HelperMethods]

    async def notify_update(self, old_item, new_item):
        print(f"{new_item.title} had an update")

    async def _add_item_to_registered_items(self, item):
        data = loadjson(self.registered_workshop_items_file)
        if item.id not in [existing_item.get('id') for existing_item in data]:
            data.append(item._asdict())
            writejson(data, self.registered_workshop_items_file)
            return True
        else:
            return False

    async def _remove_item_from_registered_items(self, item):
        data = loadjson(self.registered_workshop_items_file)
        if item.id in [existing_item.get('id') for existing_item in data]:
            data.remove(item._asdict())
            writejson(data, self.registered_workshop_items_file)
            return True
        else:
            return False

    async def _update_item_in_registered_items(self, old_item, new_item):
        data = loadjson(self.registered_workshop_items_file)
        old_item_data = old_item._asdict()
        data.remove(old_item_data)
        data.append(new_item._asdict())
        writejson(data, self.registered_workshop_items_file)

    async def _parse_update_date(self, in_update_data: str):
        date, time = in_update_data.split('@')
        if ',' not in date:
            date = date.strip() + f', {datetime.utcnow().year}'
        date = date.replace(',', '').strip()
        day, month_string, year = date.split(' ')
        month = self.month_map.get(month_string.casefold())
        if 'pm' in time:
            time = time.replace('pm', '').strip()
            hours, minutes = time.split(':')
            hours = int(hours) + 12
        else:
            time = time.replace('am', '').strip()
            hours, minutes = time.split(':')
            hours = int(hours)
        update_datetime = datetime(year=int(year), month=int(month), day=int(day), hour=int(hours), minute=int(minutes))
        return update_datetime

    async def _get_title(self, in_soup: BeautifulSoup):
        title = in_soup.find_all("div", {"class": "workshopItemTitle"})[0]
        return title.text

    async def _get_updated(self, in_soup: BeautifulSoup):
        updated_data = in_soup.findAll("div", {"class": "detailsStatRight"})[2]
        return await self._parse_update_date(updated_data.text)

    async def _get_requirements(self, in_soup: BeautifulSoup):
        _out = []
        try:
            reqs = in_soup.find_all("div", {"class": "requiredItemsContainer"})[0]
            for i in reqs.find_all('a', href=True):
                link = i.get('href', None)
                text = i.text.strip()
                _out.append((text, link))
        except IndexError:
            pass
        return _out

    async def _get_image_link(self, in_soup: BeautifulSoup):
        image = in_soup.find_all('div', {'class': "workshopItemPreviewImageMain"})[0].find_all('a')[0].get('onclick')
        match = self.image_link_regex.search(image)
        if match:
            return match.group('image_link')

    async def _get_item_size(self, in_soup: BeautifulSoup):
        size = in_soup.findAll("div", {"class": "detailsStatRight"})[0]
        return size.text

    async def _get_fresh_item_data(self, item_id: int):
        item_url = f"{self.base_url}{item_id}"
        async with self.bot.aio_request_session.get(item_url) as response:
            if RequestStatus(response.status) is RequestStatus.Ok:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                updated = await self._get_updated(soup)
                return self.workshop_item(title=await self._get_title(soup),
                                          updated=updated.strftime(self.date_time_format),
                                          requirements=await self._get_requirements(soup),
                                          url=item_url,
                                          image_link=await self._get_image_link(soup),
                                          size=await self._get_item_size(soup),
                                          id=item_id)


# endregion [HelperMethods]
# region [SpecialMethods]


    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name

    def cog_unload(self):
        self.check_for_updates.stop()
        log.debug("Cog '%s' UNLOADED!", str(self))


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(attribute_checker(SteamCog(bot)))
