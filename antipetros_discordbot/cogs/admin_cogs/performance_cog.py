

# region [Imports]

# * Standard Library Imports -->

import asyncio
import gc
import logging
import os
import re
import sys
import json
import lzma
import time
import queue
import platform
import subprocess
from enum import Enum, Flag, auto
from time import sleep
from pprint import pprint, pformat
from typing import Union
from datetime import tzinfo, datetime, timezone, timedelta
from functools import wraps, lru_cache, singledispatch, total_ordering, partial
from contextlib import contextmanager
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from statistics import mean, median, stdev, mode, variance, pvariance
import random
from io import BytesIO
from copy import deepcopy, copy
# * Third Party Imports -->

from discord.ext import commands, tasks
from discord import DiscordException
import discord
from fuzzywuzzy import process as fuzzprocess
import matplotlib.pyplot as plt
from psutil import virtual_memory
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter

# * Gid Imports -->

import gidlogger as glog


# * Local Imports -->
from antipetros_discordbot.init_userdata.user_data_setup import SupportKeeper
from antipetros_discordbot.utility.message_helper import add_to_embed_listfield
from antipetros_discordbot.utility.misc import seconds_to_pretty
from antipetros_discordbot.utility.gidtools_functions import loadjson, writejson, pathmaker, bytes2human
from antipetros_discordbot.utility.embed_helpers import make_basic_embed, make_basic_embed_inline
from antipetros_discordbot.utility.misc import save_commands, seconds_to_pretty, async_seconds_to_pretty_normal, date_today
from antipetros_discordbot.utility.checks import in_allowed_channels, log_invoker
from antipetros_discordbot.utility.named_tuples import MemoryUsageMeasurement, LatencyMeasurement
from antipetros_discordbot.utility.enums import DataSize
from antipetros_discordbot.cogs import get_aliases
from antipetros_discordbot.utility.discord_markdown_helper.special_characters import ZERO_WIDTH
# endregion[Imports]

# region [TODO]


# TODO: get_logs command
# TODO: get_appdata_location command


# endregion [TODO]

# region [AppUserData]


# endregion [AppUserData]

# region [Logging]

log = glog.aux_logger(__name__)
glog.import_notification(log, __name__)


# endregion[Logging]

# region [Constants]
APPDATA = SupportKeeper.get_appdata()
BASE_CONFIG = SupportKeeper.get_config('base_config')
COGS_CONFIG = SupportKeeper.get_config('cogs_config')
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))

DATA_COLLECT_INTERVALL = 300 if os.getenv('IS_DEV').casefold() in ['yes', 'true', '1'] else 600  # seconds
DEQUE_SIZE = (24 * 60 * 60) // DATA_COLLECT_INTERVALL  # seconds in day divided by collect interval, full deque is data of one day
DATA_DUMP_INTERVALL = {'hours': 1, 'minutes': 0, 'seconds': 0} if os.getenv('IS_DEV').casefold() in ['yes', 'true', '1'] else {'hours': 24, 'minutes': 1, 'seconds': 0}
# endregion[Constants]


class PerformanceCog(commands.Cog, command_attrs={'hidden': True, "name": "PerformanceCog"}):
    config_name = 'performance'
    save_folder = APPDATA['performance_data']

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        self.latency_thresholds = {'warning': COGS_CONFIG.getint(self.config_name, "threshold_latency_warning")}
        self.memory_thresholds = {'warning': COGS_CONFIG.getint(self.config_name, "threshold_memory_warning"), 'critical': COGS_CONFIG.getint(self.config_name, "threshold_memory_critical")}
        self.latency_data = deque(maxlen=DEQUE_SIZE)
        self.memory_data = deque(maxlen=DEQUE_SIZE)
        self.plot_formatting_info = {'latency': COGS_CONFIG.get(self.config_name, 'latency_graph_formatting'), 'memory': COGS_CONFIG.get(self.config_name, 'memory_graph_formatting')}
        if self.bot.is_debug:
            save_commands(self)
        self.latency_measure_loop.start()
        self.memory_measure_loop.start()
        self.report_data_loop.start()

    def cog_unload(self):
        self.latency_measure_loop.stop()
        self.memory_measure_loop.stop()
        self.report_data_loop.stop()

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    async def latency_measure_loop(self):
        start_time = time.time()
        log.info("measuring latency")
        now = datetime.utcnow()
        latency = round(self.bot.latency * 1000)
        if latency > self.latency_thresholds.get('warning'):
            log.warning("high latency: %s ms", str(latency))
            await self.bot.message_creator(embed=await make_basic_embed(title='LATENCY WARNING!', text='Latency is very high!', symbol='warning', **{'Time': now.strftime(self.bot.std_date_time_format), 'latency': str(latency) + ' ms'}))

        self.latency_data.append(LatencyMeasurement(now, latency))
        log.debug(f'collecting latency data took {await async_seconds_to_pretty_normal(int(round(time.time()-start_time)))}')

    @tasks.loop(seconds=DATA_COLLECT_INTERVALL, reconnect=True)
    async def memory_measure_loop(self):
        start_time = time.time()
        log.info("measuring memory usage")
        now = datetime.utcnow()
        _mem_item = virtual_memory()
        memory_in_use = _mem_item.total - _mem_item.available
        is_warning = False
        is_critical = False
        if memory_in_use > self.memory_thresholds.get("critical"):
            is_critical = True
            is_warning = True
            log.critical("Memory usage is critical! Memory in use: %s", DataSize.GigaBytes.convert(memory_in_use, annotate=True))
            await self.bot.message_creator(embed=await make_basic_embed(title='MEMORY CRITICAL!', text='Memory consumption is dangerously high!', symbol='warning', **{'Time': now.strftime(self.bot.std_date_time_format), 'Memory usage absolute': await self.convert_memory_size(memory_in_use, DataSize.GigaBytes, True, 3), 'as percent': str(_mem_item.percent) + '%'}))
        elif memory_in_use > self.memory_thresholds.get("warning"):
            is_warning = True
            log.warning("Memory usage is high! Memory in use: %s", DataSize.GigaBytes.convert(memory_in_use, annotate=True))
        self.memory_data.append(MemoryUsageMeasurement(now, _mem_item.total, _mem_item.total - _mem_item.available, _mem_item.percent, is_warning, is_critical))
        log.debug(f'collecting memory data took {await async_seconds_to_pretty_normal(int(round(time.time()-start_time)))}')

    @tasks.loop(**DATA_DUMP_INTERVALL, reconnect=True)
    async def report_data_loop(self):

        # TODO: limit amount of saved data, maybe archive it
        if datetime.utcnow() <= self.start_time + timedelta(seconds=DATA_COLLECT_INTERVALL * 2):
            return
        log.info("creating performance reports")
        collected_latency_data = list(self.latency_data.copy())
        collected_memory_data = list(self.memory_data.copy())
        for name, collected_data in [("latency", collected_latency_data), ("memory", collected_memory_data)]:
            _json_saveable_data = []
            for item in collected_data:
                item = item._replace(date_time=item.date_time.strftime(self.bot.std_date_time_format))
                _json_saveable_data.append(item)

            writejson([item._asdict() for item in _json_saveable_data], pathmaker(self.save_folder, f"[{datetime.utcnow().strftime('%Y-%m-%d')}]_collected_{name}_data.json"), sort_keys=False, indent=True)
            _file, _url = await self.make_graph(collected_data, name, pathmaker(self.save_folder, f"[{datetime.utcnow().strftime('%Y-%m-%d')}]_{name}_graph.png"))
            channel = await self.bot.channel_from_name('bot-testing')
            embed = await make_basic_embed(title=f'Report of Collected {name.title()} Data', text='data from the last 24 hours', symbol='update')
            embed.set_image(url=_url)
            await channel.send(embed=embed, file=_file)

    @ memory_measure_loop.before_loop
    async def before_memory_measure_loop(self):
        await self.bot.wait_until_ready()

    @ latency_measure_loop.before_loop
    async def before_latency_measure_loop(self):
        await self.bot.wait_until_ready()

    @ report_data_loop.before_loop
    async def before_report_data_loop(self):
        await self.bot.wait_until_ready()

    @commands.command(aliases=get_aliases("report_latency"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('performance', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('performance', 'allowed_channels')))
    async def report_latency(self, ctx, with_graph: bool = True, since_last_hours: int = 24):
        report_data = []
        for item in list(self.latency_data.copy()):
            if item.date_time >= datetime.utcnow() - timedelta(hours=since_last_hours):
                report_data.append(item)
        stat_data = [item.latency for item in report_data]
        embed_data = {'Mean': round(mean(stat_data), 2), 'Median': round(median(stat_data), 2), "Std-dev": round(stdev(stat_data))}
        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): str(item.latency) + ' ms' for item in report_data}
        embed = await make_basic_embed_inline(title='Latency Data', text=f"Data of the last {str(since_last_hours)} hours", symbol='save', amount_datapoints=str(len(self.latency_data)), ** embed_data)

        if with_graph is True:
            _file, _url = await self.make_graph(report_data, 'latency')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    @commands.command(aliases=get_aliases("report_memory"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('performance', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('performance', 'allowed_channels')))
    async def report_memory(self, ctx, with_graph: bool = True, since_last_hours: int = 24):
        report_data = []

        for item in list(self.memory_data.copy()):
            if item.date_time >= datetime.utcnow() - timedelta(hours=since_last_hours):
                report_data.append(item)
        stat_data = [bytes2human(item.absolute) for item in report_data]
        embed_data = {'Mean': round(mean(stat_data), 2), 'Median': round(median(stat_data), 2), "Std-dev": round(stdev(stat_data))}

        _file = None
        if len(report_data) < 11:
            embed_data = embed_data | {item.date_time.strftime(self.bot.std_date_time_format): '\n\n'.join([f'in use absolute: \n{bytes2human(item.absolute, annotate=True)}',
                                                                                                            f'percentage used: \n{item.as_percent}%']) for item in report_data}

        embed = await make_basic_embed_inline(title='Memory Data',
                                              text=f"Data of the last {str(since_last_hours)} hours",
                                              symbol='save', amount_datapoints=str(len(self.memory_data)),
                                              **embed_data)
        if with_graph is True:
            log.debug('calling make_graph')
            _file, _url = await self.make_graph(report_data, 'memory')
            embed.set_image(url=_url)
        await ctx.send(embed=embed, file=_file)

    async def format_graph(self):
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=max(DATA_COLLECT_INTERVALL // 60, 10)))
        plt.rcParams["font.family"] = "Consolas"
        plt.rc('xtick.major', size=6, pad=10)
        plt.rc('xtick', labelsize=9)

    async def make_graph(self, data, typus: str, save_to=None):
        start_time = time.time()
        plt.style.use('ggplot')

        await asyncio.wait_for(self.format_graph(), timeout=10)
        x = [item.date_time for item in data]

        if typus == 'latency':
            y = [item.latency for item in data]
            max_y = max(y)
            min_y = min(item.latency for item in data)
            ymin = min_y - (min_y // 6)

            ymax = max_y + (max_y // 6)
            h_line_height = max_y
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d ms'))
        else:
            y = [bytes2human(item.absolute) for item in data]
            raw_max_y = bytes2human(max(item.absolute for item in data))
            max_y = bytes2human(max(item.total for item in data))
            ymin = 0
            ymax = round(max_y * 1.1)
            h_line_height = max_y
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d gb'))
        await asyncio.sleep(0.25)

        plt.plot(x, y, self.plot_formatting_info.get(typus), markersize=2, linewidth=0.6, alpha=1)

        plt.gcf().autofmt_xdate()

        await asyncio.sleep(0.25)
        vline_max = [item.date_time for item in data if item.absolute == max(item.absolute for item in data)][0] if typus == 'memory' else [item.date_time for item in data if item.latency == max(item.latency for item in data)][0]
        plt.axvline(x=vline_max, color='g', linestyle=':')
        plt.axhline(y=h_line_height, color='r', linestyle='--')

        plt.axis(ymin=ymin, ymax=ymax)

        plt.title(f'{typus.title()} -- {datetime.utcnow().strftime("%Y.%m.%d")}')

        plt.xticks(rotation=90)
        await asyncio.sleep(0.25)
        if save_to is not None:
            plt.savefig(save_to, format='png')

        with BytesIO() as image_binary:
            plt.savefig(image_binary, format='png')
            plt.close()
            image_binary.seek(0)
            log.debug(f'making graph took {await async_seconds_to_pretty_normal(int(round(time.time()-start_time)))}')
            return discord.File(image_binary, filename=f'{typus}graph.png'), f"attachment://{typus}graph.png"

    async def convert_memory_size(self, in_bytes, new_unit: DataSize, annotate: bool = False, extra_digits=2):

        if annotate is False:
            return round(int(in_bytes) / new_unit.value, ndigits=extra_digits)
        return str(round(int(in_bytes) / new_unit.value, ndigits=extra_digits)) + ' ' + new_unit.short_name

    async def get_time_from_max_y(self, data, max_y, typus):
        for item in data:
            if typus == 'memory':
                if await self.convert_memory_size(item.absolute, DataSize.GigaBytes) == max_y:
                    _out = item.date_time
            else:
                if item.latency == max_y:
                    _out = item.date_time
        return _out

    @commands.command(aliases=get_aliases("get_command_stats"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('performance', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('performance', 'allowed_channels')))
    async def get_command_stats(self, ctx):
        data_dict = {item.name: f"{ZERO_WIDTH}\n{item.data}\n{ZERO_WIDTH}" for item in await self.bot.command_staff.get_todays_invoke_data()}
        date = date_today()

        embed = await make_basic_embed(title=ctx.command.name, text=f'data of the last 24hrs - {date}', symbol='data', **data_dict)

        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases("report"))
    @ commands.has_any_role(*COGS_CONFIG.getlist('performance', 'allowed_roles'))
    @ in_allowed_channels(set(COGS_CONFIG.getlist('performance', 'allowed_channels')))
    async def report(self, ctx):
        await ctx.invoke(self.bot.get_command('report_memory'))
        await ctx.invoke(self.bot.get_command('report_latency'))

    def __str__(self) -> str:
        return self.qualified_name


def setup(bot):
    bot.add_cog(PerformanceCog(bot))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
