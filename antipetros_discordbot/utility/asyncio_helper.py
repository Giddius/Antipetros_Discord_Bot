
# region [Imports]

import os
import asyncio
from collections import defaultdict, OrderedDict, namedtuple, Counter, ChainMap, deque, UserDict, UserList, UserString
from enum import Enum, Flag, unique, auto
from itertools import chain, product, combinations, product, groupby, permutations, cycle, repeat, zip_longest, takewhile
from functools import cached_property, partial, lru_cache
from contextlib import contextmanager, asynccontextmanager
from sortedcontainers import SortedDict, SortedList
from typing import Callable, TYPE_CHECKING, Optional, Union, Awaitable, Coroutine
from io import BytesIO, StringIO
from datetime import datetime, timedelta, timezone
from abc import ABCMeta, ABC, abstractmethod
import collections.abc

import inspect
import discord
from discord.ext import commands


from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, readit, writeit
from asyncio.locks import _ContextManagerMixin
# endregion[Imports]


async def message_delete(msg: discord.Message, delay: float = None, shutdown_event: asyncio.Event = None):
    async def delete_task():
        if shutdown_event is not None:
            done, pending = await asyncio.wait([shutdown_event.wait()], timeout=delay, return_when=asyncio.FIRST_COMPLETED)
            for pending_aws in pending:
                pending_aws.cancel()
            delay = None
        await msg.delete(delay=delay)
    asyncio.create_task(delete_task(), name=f"DELETE_AFTER_MESSAGE_REMOVAL_{msg.channel.name}_{msg.id}")


class RestartBlocker(_ContextManagerMixin):

    def __init__(self) -> None:
        self.open_tokens: int = 0

    async def acquire(self):
        self.open_tokens += 1

    def release(self):
        self.open_tokens -= 1

    @property
    def unblocked(self) -> bool:
        return self.open_tokens == 0

    @asynccontextmanager
    async def wait_until_unblocked(self):
        while self.unblocked is False:
            await asyncio.sleep(0.1)
        yield


async def async_range(*args):
    for i in range(*args):
        yield i


async def delayed_execution(delay: float, func: Union[Callable, Awaitable], **kwargs):
    await asyncio.sleep(delay)
    if inspect.iscoroutinefunction(func):
        await func(**kwargs)
    else:
        func(**kwargs)
