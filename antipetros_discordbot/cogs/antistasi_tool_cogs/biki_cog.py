
# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
from datetime import datetime, timedelta, timezone
from collections import namedtuple
import re
from typing import List, TYPE_CHECKING, Union
import yarl
import random
# * Third Party Imports --------------------------------------------------------------------------------->
from discord.ext import commands, tasks
import discord
from bs4 import BeautifulSoup, PageElement, NavigableString
# * Gid Imports ----------------------------------------------------------------------------------------->
import gidlogger as glog
# * Local Imports --------------------------------------------------------------------------------------->
from antipetros_discordbot.utility.checks import allowed_channel_and_allowed_role, owner_or_admin
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.misc import loop_starter
from antipetros_discordbot.utility.url import fix_url, make_url_absolute
from antipetros_discordbot.utility.enums import RequestStatus, CogMetaStatus, UpdateTypus
from antipetros_discordbot.engine.replacements import AntiPetrosBaseCog, CommandCategory, RequiredFile, auto_meta_info_command
from antipetros_discordbot.utility.discord_markdown_helper.string_manipulation import shorten_string
from antipetros_discordbot.utility.discord_markdown_helper import ZERO_WIDTH
from antipetros_discordbot.utility.sqldata_storager import general_db
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
from antipetros_discordbot.engine.replacements.task_loop_replacement import custom_loop

# endregion[Imports]

# region [TODO]

# TODO: Add all special Cog methods

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


# endregion[Constants]


class A3Function:
    db = general_db
    bot: "AntiPetrosBot" = None
    table_name = "a3_functions_tbl"

    def __init__(self, name: str, url: Union[str, yarl.URL], description: str, extra_data: dict[str, str]) -> None:
        self.name = name
        self.url = yarl.URL(url) if isinstance(url, str) else url
        self.description = description
        self.extra_data = extra_data

    @classmethod
    def _modify_content(cls, base_url: yarl.URL, element: PageElement, soup: BeautifulSoup) -> str:
        for codeblock in element.find_all('code'):
            text = codeblock.get_text()
            codeblock.string = f"```sqf\n{text}\n```"

        for codeblock in element.find_all('pre'):
            text = codeblock.get_text()
            codeblock.string = f"```sqf\n{text}\n```"

        for link in element.find_all('a'):

            url = link.get('href')
            if url:
                try:
                    name = link.get_text()
                except AttributeError:
                    name = link.get('title')

                link.string = f"[***{name}***]({make_url_absolute(base_url,url)})"
                link.insert_after(soup.new_string('\n'))
        element.find('dt').extract()
        return element.get_text().strip()

    @classmethod
    def _parse_html(cls, url: yarl.URL, content: str):
        soup = BeautifulSoup(content, "html.parser")
        data = {"title": soup.find('h1').decode_contents()}

        for item in soup.find_all('dl'):
            try:
                typus = item.find('dt').get_text().replace(':', '').casefold().strip().replace(' ', '_')
                if typus:
                    data[typus] = cls._modify_content(base_url=url, element=item, soup=soup)
            except AttributeError:
                log.critical("attribute error on %s.from_url(url=%s)", cls.__name__, url)
        return data

    @classmethod
    async def from_url(cls, url: Union[str, yarl.URL]) -> "A3Function":
        if isinstance(url, str):
            url = yarl.URL(url)
        text = await cls.bot.get_request_text(url)

        data = await asyncio.to_thread(cls._parse_html, url, text)
        instance = cls(name=data.pop('title'), url=url, description=data.pop('description'), extra_data=data)
        await instance.to_db()
        return instance

    async def to_db(self):
        await self.db.insert_a3_function(self)
        log.debug("added function '%s' to db", self.name)

    @property
    def aliases(self):
        aliases = [self.name.casefold()]
        aliases.append(self.name.split('_', 1)[-1])
        aliases = map(lambda x: x.casefold(), aliases)
        return list(set(aliases))

    def as_embed(self):
        embed = discord.Embed(title=self.name, description=ZERO_WIDTH, url=self.url, colour=discord.Color.random())
        embed.add_field(name="Description" + "\n" + ZERO_WIDTH, value=self.description.replace('"', '`'))
        for key, value in self.extra_data.items():
            if value is not None:
                embed.add_field(name=key.replace('_', ' ').title(), value=ZERO_WIDTH + '\n' + value.replace('"', '`'), inline=False)
        embed.set_thumbnail(url="https://i.postimg.cc/DfjJfTXw/ASCM2-Logo.png")
        return embed


class BikiUrls:
    db = general_db
    bot: "AntiPetrosBot" = None

    base_url = yarl.URL("https://community.bistudio.com")
    api_url = base_url / "wikidata" / "api.php"
    wiki_url = base_url / 'wiki'
    a3_function_category_url = wiki_url / "Category:Arma_3:_Functions"

    def __init__(self):
        self.function_items = {}
        self.function_name_regex: re.Pattern = None

    def _as_absolute_url(self, relative_url: str) -> yarl.URL:
        return make_url_absolute(self.base_url, relative_url)

    async def _scrape_function_links(self):
        _out = []
        links = await self.bot.find_urls_in_website(self.a3_function_category_url)

        for link in links:
            # link.split('/')[-1].startswith('BIN_fnc') or
            if link.split('/')[-1].startswith('BIS_fnc'):
                _out.append(self._as_absolute_url(link))
                await asyncio.sleep(0)
        return _out

    async def refresh_functions(self):
        links = await self._scrape_function_links()
        amount_links = len(links)
        log.debug("found %s function links", str(amount_links))
        for index_num, link in enumerate(links):
            log.debug("scraping func number %s out of %s", str(index_num), str(amount_links))
            await A3Function.from_url(url=link)
            await asyncio.sleep(random.randint(0, (datetime.now(tz=timezone.utc).second // random.randint(1, 10))))
        await asyncio.sleep(10)
        await self.load_functions()

    async def load_functions(self):
        self.function_items = {}
        rows = await self.db.get_a3_functions()

        for row in rows:
            row = dict(**row)
            func_item = await asyncio.to_thread(A3Function, name=row.pop('name'), url=row.pop('url'), description=row.pop('description'), extra_data=row)
            self.function_items[func_item.name] = func_item
            await asyncio.sleep(0)
        asyncio.create_task(self.create_function_name_regex())

    async def create_function_name_regex(self):
        names = []
        for item in self.function_items.values():
            names.append(item.name)
            names += item.aliases
            await asyncio.sleep(0)

        def _make_regex(all_names: list[str]):
            comb_names = r'|'.join(all_names)
            self.function_name_regex = re.compile(rf"(?:\s|\A)(?P<name>{comb_names})", re.IGNORECASE)
        asyncio.create_task(asyncio.to_thread(_make_regex, names))


class BikiCog(AntiPetrosBaseCog, command_attrs={'hidden': False, "categories": CommandCategory.TEAMTOOLS | CommandCategory.ADMINTOOLS | CommandCategory.DEVTOOLS}):
    """
    Commands to interact with Steam, the Steam Workshop and to alert if mods are updated. Still WiP
    """
    # region [ClassAttributes]

    public = False
    meta_status = CogMetaStatus.UNTESTED | CogMetaStatus.FEATURE_MISSING | CogMetaStatus.CRASHING | CogMetaStatus.DOCUMENTATION_MISSING
    long_description = ""
    extra_info = ""
    required_config_data = {'base_config': {},
                            'cogs_config': {}}

    required_folder = []
    required_files = []

    # endregion [ClassAttributes]

    # region [Init]

    def __init__(self, bot: "AntiPetrosBot"):
        super().__init__(bot)
        self.color = "white"
        self.urls = BikiUrls()


# endregion [Init]

# region [Properties]


# endregion [Properties]

# region [Setup]

    async def on_ready_setup(self):
        await super().on_ready_setup()
        BikiUrls.bot = self.bot
        A3Function.bot = self.bot
        await self.urls.load_functions()
        self.ready = True
        log.debug('setup for cog "%s" finished', str(self))

    async def update(self, typus: UpdateTypus):
        await super().update(typus)
        log.debug('cog "%s" was updated', str(self))

# endregion [Setup]

# region [Loops]


# endregion [Loops]

# region [Listener]

    @ commands.Cog.listener(name='on_message')
    async def listen_for_function_in_message(self, msg: discord.Message):
        if self.completely_ready is False:
            return

        channel = msg.channel
        author = msg.author
        if self.bot.is_debug is True and channel.id != 645930607683174401:
            return
        if channel.type is discord.ChannelType.private:
            return
        if author.bot is True:
            return

        func_match = self.urls.function_name_regex.search(msg.content)
        if not func_match:
            return

        func_name = func_match.group('name')
        if not func_name:
            return
        log.debug("matched func name is '%s'", func_name)
        name_query = {}
        for func in self.urls.function_items.values():
            name_query[func.name] = func
            for alias in func.aliases:
                name_query[alias] = func
        await asyncio.sleep(0)
        func_object = name_query.get(func_name.casefold())
        await channel.send(embed=func_object.as_embed())

# endregion [Listener]

# region [Commands]

    @ auto_meta_info_command()
    @ owner_or_admin()
    async def refresh_function_db(self, ctx: commands.Context):
        await ctx.send('starting to scrape functions')

        build_task = asyncio.create_task(self.urls.refresh_functions(), name='a3functions_db_build_task')
        await build_task
        await ctx.send(f"done, collected {len(self.urls.function_items)} functions!")

# endregion [Commands]

# region [HelperMethods]


# endregion [HelperMethods]

# region [SpecialMethods]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bot.__class__.__name__})"

    def __str__(self):
        return self.qualified_name


# endregion [SpecialMethods]


def setup(bot):
    """
    Mandatory function to add the Cog to the bot.
    """
    bot.add_cog(BikiCog(bot))
