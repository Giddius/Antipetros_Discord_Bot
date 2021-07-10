"""
[summary]

[extended_summary]
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import asyncio
import discord
from datetime import datetime, timedelta, timezone
import aiohttp
from typing import TYPE_CHECKING, Union, Optional, Callable, Iterable, Generator, Awaitable, Coroutine, List, Set, Tuple, IO, Dict, Mapping, NamedTuple
import gidlogger as glog
import yarl
from urlextract import URLExtract

from antipetros_discordbot.abstracts.subsupport_abstract import SubSupportBase
from antipetros_discordbot.init_userdata.user_data_setup import ParaStorageKeeper
from antipetros_discordbot.utility.enums import UpdateTypus, RequestStatus
from antipetros_discordbot.utility.misc import alt_seconds_to_pretty
if TYPE_CHECKING:
    from antipetros_discordbot.engine.antipetros_bot import AntiPetrosBot
    from antipetros_discordbot.bot_support.bot_supporter import BotSupporter
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

THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

# endregion[Constants]


class WebAccessor(SubSupportBase):

    def __init__(self, bot: "AntiPetrosBot", support: "BotSupporter"):
        self.bot = bot
        self.support = support
        self.loop = self.bot.loop
        self.is_debug = self.bot.is_debug
        self.aio_session: aiohttp.ClientSession = None
        self.url_extractor = URLExtract()
        self.other_sessions = {}

    def fix_url(self, url: str):
        _url = yarl.URL(url)
        if _url.is_absolute() is False:
            _url = yarl.URL('//' + url)
            _url = _url.with_scheme('https')
        return _url

    async def find_urls(self, text: str):
        urls = await asyncio.to_thread(self.url_extractor.find_urls, text=text)
        return [self.fix_url(url) for url in urls]

    async def request_json(self, url):
        async with self.aio_session.get(url=url) as response:
            if RequestStatus(response.status) is RequestStatus.Ok:
                return await response.json()

    async def close_sessions(self):
        log.info('closing sessions')
        await self.aio_session.close()
        for session_name, session in self.other_sessions.items():

            await session.close()
            log.info("'%s' was shut down", session_name)

    async def on_ready_setup(self):
        self.aio_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(enable_cleanup_closed=True))
        asyncio.create_task(asyncio.to_thread(self.url_extractor.update))
        log.debug("'%s' sub_support is READY", str(self))

    async def update(self, typus: UpdateTypus):
        asyncio.create_task(asyncio.to_thread(self.url_extractor.update))
        log.debug("'%s' sub_support was UPDATED", str(self))

    async def retire(self):
        await self.close_sessions()
        log.debug("'%s' sub_support was RETIRED", str(self))


def get_class():
    return WebAccessor

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
